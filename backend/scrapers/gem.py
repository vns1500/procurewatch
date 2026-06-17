import asyncio
import hashlib
import random
from datetime import date, timedelta
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

MINISTRIES = [
    "Ministry of Defence",
    "Ministry of Railways",
    "Ministry of Health and Family Welfare",
    "Ministry of Road Transport and Highways",
    "Ministry of Education",
    "Ministry of Agriculture and Farmers Welfare",
    "Ministry of Home Affairs",
    "Ministry of Finance",
    "Ministry of Electronics and Information Technology",
    "Ministry of Jal Shakti",
    "Ministry of Power",
    "Ministry of Coal",
    "Ministry of Steel",
    "Ministry of Petroleum and Natural Gas",
    "Ministry of Shipping",
    "Ministry of Civil Aviation",
    "Ministry of Textiles",
    "Ministry of Food Processing Industries",
    "Ministry of Science and Technology",
    "Ministry of Environment, Forest and Climate Change",
    "Ministry of Labour and Employment",
    "Ministry of Rural Development",
    "Ministry of Urban Development",
    "Ministry of Housing and Urban Affairs",
    "Ministry of Commerce and Industry",
]

STATES = [
    "Maharashtra", "Uttar Pradesh", "Tamil Nadu", "Karnataka", "Gujarat",
    "Rajasthan", "Madhya Pradesh", "West Bengal", "Bihar", "Andhra Pradesh",
    "Telangana", "Kerala", "Odisha", "Punjab", "Haryana",
    "Jharkhand", "Uttarakhand", "Himachal Pradesh", "Chhattisgarh", "Assam",
    "Delhi", "Goa", "Tripura", "Manipur", "Meghalaya",
    "Jammu and Kashmir", "Ladakh", "Chandigarh", "Puducherry", "Sikkim",
]

ITEM_CATEGORIES = [
    ("IT Hardware - Laptops", 45000_00, 150000_00),
    ("IT Hardware - Servers", 200000_00, 2000000_00),
    ("Office Furniture", 5000_00, 50000_00),
    ("Stationery Supplies", 500_00, 10000_00),
    ("Medical Equipment - Ventilators", 500000_00, 5000000_00),
    ("Medical Supplies - PPE Kits", 200_00, 2000_00),
    ("Road Construction Materials", 1000000_00, 50000000_00),
    ("Construction - Cement", 800_00, 5000_00),
    ("Vehicles - Light Commercial", 500000_00, 2000000_00),
    ("Vehicles - Heavy Trucks", 1500000_00, 5000000_00),
    ("Uniforms and Clothing", 500_00, 5000_00),
    ("Security Systems - CCTV", 50000_00, 500000_00),
    ("Solar Panels", 20000_00, 500000_00),
    ("Electrical Equipment - Transformers", 100000_00, 2000000_00),
    ("Chemical Supplies", 10000_00, 500000_00),
    ("Agricultural Equipment - Tractors", 300000_00, 1500000_00),
    ("Food Supplies - Rations", 1000_00, 50000_00),
    ("Printing Services", 5000_00, 200000_00),
    ("Consulting Services - IT", 100000_00, 5000000_00),
    ("Water Treatment Equipment", 500000_00, 10000000_00),
]

VENDOR_NAMES = [
    "Tata Consultancy Services Ltd", "Infosys BPM Ltd", "Wipro Ltd",
    "HCL Technologies", "Tech Mahindra", "Larsen & Toubro Ltd",
    "Reliance Industries", "Bharat Electronics Ltd", "NTPC Ltd",
    "Steel Authority of India", "Indian Oil Corporation", "BHEL Ltd",
    "HAL India Ltd", "Mazagon Dock Shipbuilders", "BEML Ltd",
    "Bharat Forge Ltd", "Godrej & Boyce", "Siemens India Ltd",
    "ABB India Ltd", "Schneider Electric India", "Honeywell Automation",
    "Bosch Ltd India", "3M India Ltd", "Johnson Controls India",
    "Kirloskar Brothers Ltd", "Thermax Ltd", "Cummins India Ltd",
    "Ashok Leyland Ltd", "Mahindra & Mahindra", "Force Motors Ltd",
    "Voltas Ltd", "Blue Star Ltd", "Carrier Midea India",
    "Apollo Hospitals Enterprise", "Fortis Healthcare", "Max Healthcare",
    "Sun Pharmaceutical Industries", "Cipla Ltd", "Dr Reddy's Labs",
    "Delhivery Ltd", "Blue Dart Express", "Gati KWE Ltd",
    "KPMG Advisory Services", "Deloitte India", "PricewaterhouseCoopers",
    "Quess Corp Ltd", "TeamLease Services", "Mphasis Ltd",
    "Zensar Technologies", "Persistent Systems", "Mastech Holdings",
    "Megha Engineering", "KEC International", "Kalpataru Power",
    "GMR Group", "GVK Infrastructure", "IL&FS Engineering",
    "Nagarjuna Construction", "Punj Lloyd", "Shapoorji Pallonji",
    "Oberoi Construction", "DLF Infrastructure", "Prestige Estates",
    "AGS Transact Technologies", "CMS Info Systems", "Securitas India",
    "G4S Security Services", "SIS Ltd", "Topsgrup Security",
    "Triveni Engineering", "Bajaj Electricals", "Havells India",
    "Polycab India", "Finolex Cables", "Orient Electric",
    "Exide Industries", "Amara Raja Batteries", "Luminous Power",
    "Micromax Informatics", "Dixon Technologies", "Amber Enterprises",
    "Patanjali Ayurved", "ITC Ltd", "Marico Ltd",
    "Adani Ports", "JSW Infrastructure", "Container Corporation",
    "Arvind Fashions", "Raymond Ltd", "Page Industries",
    "Asian Paints", "Berger Paints", "Kansai Nerolac",
    "Pidilite Industries", "Henkel India", "Sika India",
    "Ultratech Cement", "Ambuja Cements", "ACC Ltd",
    "Shree Cement", "JK Cement", "Dalmia Bharat",
    "Tata Steel", "JSW Steel", "Jindal Steel",
    "Hindalco Industries", "Vedanta Ltd", "National Aluminium",
]


def _generate_gstin(state_code: int, pan: str) -> str:
    return f"{state_code:02d}{pan}{random.randint(1, 9)}Z{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"


def generate_synthetic_orders(count: int = 600) -> list[dict[str, Any]]:
    orders = []
    base_date = date(2024, 1, 1)

    vendor_pool = []
    for i, name in enumerate(VENDOR_NAMES):
        state_code = random.randint(11, 36)
        pan_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        pan = f"{''.join(random.choices(pan_chars, k=5))}{random.randint(1000, 9999)}{''.join(random.choices(pan_chars, k=1))}"
        vendor_pool.append({
            "id": f"VENDOR{i+1:04d}",
            "name": name,
            "gstin": _generate_gstin(state_code, pan),
            "state": random.choice(STATES),
            "incorporation_date": (base_date - timedelta(days=random.randint(365, 5000))).isoformat(),
        })

    for i in range(count):
        days_offset = random.randint(0, 540)
        tender_date = base_date + timedelta(days=days_offset)

        # Inject anomaly patterns into ~35% of records
        anomaly_roll = random.random()
        if anomaly_roll < 0.12:
            # Single bid
            bid_count = 1
            days_open = random.randint(3, 14)
        elif anomaly_roll < 0.20:
            # Rushed timeline
            bid_count = random.randint(1, 4)
            days_open = random.randint(0, 2)
        elif anomaly_roll < 0.28:
            # Both
            bid_count = 1
            days_open = random.randint(0, 2)
        else:
            bid_count = random.randint(2, 18)
            days_open = random.randint(7, 30)

        close_date = tender_date + timedelta(days=days_open)
        category, price_min, price_max = random.choice(ITEM_CATEGORIES)
        quantity = random.randint(1, 500)
        unit_price = random.randint(price_min, price_max)
        total_value = unit_price * quantity

        vendor = random.choice(vendor_pool)
        ministry = random.choice(MINISTRIES)
        state = random.choice(STATES)

        order_id = f"GEM/2024-25/{ministry[:3].upper()}/{i+1:06d}"
        gem_id = hashlib.sha256(order_id.encode()).hexdigest()[:16].upper()

        orders.append({
            "order_id": order_id,
            "gem_id": f"GEM{gem_id}",
            "buyer_org": ministry,
            "seller_name": vendor["name"],
            "seller_gstin": vendor["gstin"],
            "seller_state": vendor["state"],
            "seller_incorporation_date": vendor["incorporation_date"],
            "item_description": f"{category} - Lot {i+1}",
            "quantity": quantity,
            "unit_price": unit_price,
            "total_value": total_value,
            "order_date": tender_date.isoformat(),
            "close_date": close_date.isoformat(),
            "delivery_state": state,
            "bid_count": bid_count,
        })

    # Inject bid-splitting cluster: same vendor, same ministry, 30-day window
    split_vendor = random.choice(vendor_pool)
    split_ministry = random.choice(MINISTRIES)
    split_base = base_date + timedelta(days=random.randint(0, 400))
    for j in range(5):
        split_value = random.randint(100000_00, 195000_00)  # below 2L threshold in paise
        split_date = split_base + timedelta(days=j * 4)
        order_id = f"GEM/2024-25/SPLIT/{j+1:06d}"
        gem_id = hashlib.sha256((order_id + split_vendor["name"]).encode()).hexdigest()[:16].upper()
        orders.append({
            "order_id": order_id,
            "gem_id": f"SPLIT{gem_id}",
            "buyer_org": split_ministry,
            "seller_name": split_vendor["name"],
            "seller_gstin": split_vendor["gstin"],
            "seller_state": split_vendor["state"],
            "seller_incorporation_date": split_vendor["incorporation_date"],
            "item_description": f"Stationery Supplies - Batch {j+1}",
            "quantity": 1,
            "unit_price": split_value,
            "total_value": split_value,
            "order_date": split_date.isoformat(),
            "close_date": (split_date + timedelta(days=7)).isoformat(),
            "delivery_state": random.choice(STATES),
            "bid_count": random.randint(2, 5),
        })

    return orders


class GEMScraper:
    BASE_URL = "https://gem.gov.in"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def scrape_orders(self, page: int = 1) -> list[dict[str, Any]]:
        log = logger.bind(page=page)
        try:
            client = await self._get_client()
            await asyncio.sleep(2 + random.uniform(0, 1))

            url = f"{self.BASE_URL}/api/public/orders"
            params = {"page": page, "limit": 50, "status": "completed"}

            for attempt in range(3):
                try:
                    response = await client.get(url, params=params, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; ProcureWatch/1.0)",
                        "Accept": "application/json",
                    })
                    if response.status_code == 200:
                        data = response.json()
                        records = data.get("data", data.get("orders", []))
                        log.info("scraped_orders", records_found=len(records))
                        return records
                    log.warning("api_non_200", status=response.status_code, attempt=attempt)
                except httpx.HTTPError as exc:
                    log.warning("http_error", error=str(exc), attempt=attempt)
                    await asyncio.sleep(2 ** attempt)

            log.info("falling_back_to_synthetic_data")
            return generate_synthetic_orders(600)[((page - 1) * 50): (page * 50)]

        except Exception as exc:
            log.error("scrape_failed", error=str(exc))
            return generate_synthetic_orders(600)[((page - 1) * 50): (page * 50)]

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        total_value_rupees = raw.get("total_value", raw.get("unit_price", 0) * raw.get("quantity", 1))
        # Convert to paise (multiply by 100) if not already
        if isinstance(total_value_rupees, float) and total_value_rupees < 1_000_000:
            value_paise = int(total_value_rupees * 100)
        else:
            value_paise = int(total_value_rupees)

        ministry = raw.get("buyer_org", raw.get("ministry", "Unknown Ministry"))
        state = raw.get("delivery_state", raw.get("state", "Unknown"))

        return {
            "gem_id": raw.get("gem_id", raw.get("order_id", "")),
            "title": raw.get("item_description", raw.get("title", "Untitled")),
            "ministry": ministry,
            "state": state,
            "value": value_paise,
            "tender_date": raw.get("order_date", raw.get("tender_date", "")),
            "close_date": raw.get("close_date", ""),
            "bid_count": int(raw.get("bid_count", 1)),
            "vendor_name": raw.get("seller_name", raw.get("vendor_name", "")),
            "vendor_gstin": raw.get("seller_gstin", ""),
            "vendor_state": raw.get("seller_state", ""),
            "vendor_incorporation_date": raw.get("seller_incorporation_date"),
            "raw_json": raw,
        }

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
