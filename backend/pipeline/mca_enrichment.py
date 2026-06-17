"""MCA21 vendor enrichment — director network graph via networkx."""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import networkx as nx
import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from models.vendor import Vendor

logger = structlog.get_logger(__name__)

DIRECTOR_NAMES = [
    "Ramesh Kumar Gupta", "Sunita Devi Sharma", "Mohan Lal Verma", "Priya Singh",
    "Rajesh Patel", "Anita Desai", "Suresh Chandra Nair", "Meena Kumari",
    "Vikram Singh Chauhan", "Kavitha Reddy", "Arun Kumar Mishra", "Pooja Agarwal",
    "Dinesh Babu Rao", "Lakshmi Narayanan", "Sanjay Mehta", "Rekha Joshi",
    "Manoj Kumar Tiwari", "Geeta Bhatt", "Ravi Shankar Prasad", "Uma Devi",
    "Harish Chandra", "Padma Venkatesh", "Gopal Krishna", "Sarla Devi",
    "Deepak Malhotra", "Usha Rani", "Naresh Chand", "Anjali Kapoor",
    "Bharat Bhushan", "Savita Devi", "Ashok Kumar", "Nirmala Srivastava",
    "Prem Nath", "Kamla Sharma", "Sunil Kumar Singh", "Rita Pandey",
]

COMPANY_SUFFIXES = [
    "Pvt Ltd", "Limited", "Enterprises", "Solutions", "Infrastructure",
    "Technologies", "Services", "Constructions", "Traders", "Associates",
]


@dataclass
class DirectorRecord:
    din: str
    name: str
    vendor_ids: list[str] = field(default_factory=list)


@dataclass
class VendorEnrichment:
    vendor_id: str
    cin: str
    directors: list[DirectorRecord]
    director_network_json: dict[str, Any]
    shared_directors: list[str]
    has_director_overlap: bool


def _gen_din(seed: str) -> str:
    rng = random.Random(seed)
    return "".join([str(rng.randint(0, 9)) for _ in range(8)])


def _gen_cin(seed: str) -> str:
    rng = random.Random(seed + "_cin")
    sector = rng.choice(["U", "L"])
    code = rng.randint(10000, 99999)
    state = rng.choice(["DL", "MH", "KA", "GJ", "UP", "RJ", "TN", "WB"])
    year = rng.randint(1990, 2015)
    num = "".join([str(rng.randint(0, 9)) for _ in range(6)])
    return f"{sector}{code}{state}{year}PLC{num}"


class MCA21Enricher:
    def __init__(self) -> None:
        self._vendor_directors: dict[str, list[DirectorRecord]] = {}

    async def enrich_vendor(self, vendor: "Vendor", db: "AsyncSession") -> VendorEnrichment:
        if str(vendor.id) in self._vendor_directors:
            directors = self._vendor_directors[str(vendor.id)]
        else:
            directors = self._synthetic_directors(vendor)
            self._vendor_directors[str(vendor.id)] = directors

        cin = _gen_cin(str(vendor.id))
        network_json = self._build_network_json(vendor, directors)

        shared: list[str] = []
        for d in directors:
            if len(d.vendor_ids) > 1:
                shared.append(d.din)

        import json
        from sqlalchemy import text
        await db.execute(
            text("UPDATE vendors SET cin = :cin, director_network_json = cast(:net as jsonb) WHERE id = :vid"),
            {"cin": cin, "net": json.dumps(network_json), "vid": str(vendor.id)},
        )

        logger.info("vendor_enriched", vendor_id=str(vendor.id), cin=cin, directors=len(directors))
        return VendorEnrichment(
            vendor_id=str(vendor.id),
            cin=cin,
            directors=directors,
            director_network_json=network_json,
            shared_directors=shared,
            has_director_overlap=len(shared) > 0,
        )

    def _synthetic_directors(self, vendor: "Vendor") -> list[DirectorRecord]:
        rng = random.Random(str(vendor.id))
        n_directors = rng.randint(2, 5)
        directors: list[DirectorRecord] = []
        for i in range(n_directors):
            # Re-use a small pool so some directors appear in multiple companies
            name_idx = rng.randint(0, len(DIRECTOR_NAMES) - 1) % 20
            name = DIRECTOR_NAMES[name_idx]
            din = _gen_din(f"{vendor.id}_{i}_{name_idx}")
            rec = DirectorRecord(din=din, name=name, vendor_ids=[str(vendor.id)])
            directors.append(rec)
        return directors

    def _build_network_json(self, vendor: "Vendor", directors: list[DirectorRecord]) -> dict[str, Any]:
        return {
            "vendor_id": str(vendor.id),
            "vendor_name": vendor.name,
            "nodes": [
                {
                    "id": f"vendor_{vendor.id}",
                    "type": "vendor",
                    "label": vendor.name,
                    "risk_level": vendor.risk_level or "low",
                }
            ] + [
                {
                    "id": f"director_{d.din}",
                    "type": "director",
                    "label": d.name,
                    "din": d.din,
                }
                for d in directors
            ],
            "edges": [
                {
                    "source": f"vendor_{vendor.id}",
                    "target": f"director_{d.din}",
                    "type": "has_director",
                }
                for d in directors
            ],
        }

    async def build_director_graph(
        self,
        vendor_ids: list[str],
        db: "AsyncSession",
    ) -> nx.Graph:
        from sqlalchemy import select, text
        from models.vendor import Vendor as VendorModel

        result = await db.execute(
            select(VendorModel).where(VendorModel.id.in_(vendor_ids))
        )
        vendors = result.scalars().all()

        G = nx.Graph()

        # Build graph from enriched data or synthetic
        for vendor in vendors:
            G.add_node(str(vendor.id), type="vendor", name=vendor.name, risk_level=vendor.risk_level or "low")
            directors = self._synthetic_directors(vendor)
            for d in directors:
                G.add_node(d.din, type="director", name=d.name)
                G.add_edge(str(vendor.id), d.din, relation="has_director")

        return G

    def detect_director_overlap(
        self,
        vendor_a_id: str,
        vendor_b_id: str,
        graph: nx.Graph,
    ) -> list[str]:
        """Return list of shared director DINs between two vendors."""
        if vendor_a_id not in graph or vendor_b_id not in graph:
            return []

        neighbors_a = {n for n in graph.neighbors(vendor_a_id) if graph.nodes[n].get("type") == "director"}
        neighbors_b = {n for n in graph.neighbors(vendor_b_id) if graph.nodes[n].get("type") == "director"}
        return list(neighbors_a & neighbors_b)

    def find_connected_companies(
        self,
        vendor_id: str,
        graph: nx.Graph,
        max_depth: int = 2,
    ) -> list[dict[str, Any]]:
        """Find vendor nodes reachable within max_depth hops via shared directors."""
        if vendor_id not in graph:
            return []

        connected: list[dict[str, Any]] = []
        seen = {vendor_id}

        for path_length in range(1, max_depth + 1):
            for node in nx.single_source_shortest_path_length(graph, vendor_id, cutoff=path_length * 2):
                if node in seen:
                    continue
                if graph.nodes[node].get("type") == "vendor":
                    seen.add(node)
                    connected.append({
                        "vendor_id": node,
                        "name": graph.nodes[node].get("name", ""),
                        "risk_level": graph.nodes[node].get("risk_level", "low"),
                        "hops": path_length,
                    })

        return connected


async def enrich_all_vendors(db: "AsyncSession") -> int:
    from sqlalchemy import select
    from models.vendor import Vendor as VendorModel

    enricher = MCA21Enricher()
    result = await db.execute(select(VendorModel).limit(200))
    vendors = result.scalars().all()

    for vendor in vendors:
        await enricher.enrich_vendor(vendor, db)

    await db.commit()
    logger.info("all_vendors_enriched", count=len(vendors))
    return len(vendors)
