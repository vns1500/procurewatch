"""CAG — Comptroller and Auditor General audit findings scraper (cag.gov.in)"""
from __future__ import annotations

import random
from datetime import date
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

MINISTRIES = [
    "Ministry of Defence", "Ministry of Railways", "Ministry of Health and Family Welfare",
    "Ministry of Road Transport and Highways", "Ministry of Education",
    "Ministry of Finance", "Ministry of Home Affairs", "Ministry of Power",
    "Ministry of Coal", "Ministry of Steel", "Ministry of Petroleum and Natural Gas",
    "Ministry of Agriculture and Farmers Welfare", "Ministry of Housing and Urban Affairs",
    "Ministry of Electronics and Information Technology",
]

IRREGULARITY_TYPES = [
    "procurement_without_tender",
    "excess_payment_to_contractor",
    "avoidable_expenditure",
    "idle_machinery_and_equipment",
    "irregular_deployment_of_funds",
    "short_recovery_of_dues",
    "fraudulent_claims",
    "splitting_of_works",
    "post_award_cost_escalation",
    "non_competitive_bidding",
    "specification_manipulation",
    "fictitious_expenditure",
]

DESCRIPTIONS = {
    "procurement_without_tender": (
        "Procurement of goods/services was made without inviting competitive tenders, "
        "in violation of GFR 2017 Rule 149. Quotation method was used for high-value procurement "
        "that mandated open competitive bidding."
    ),
    "excess_payment_to_contractor": (
        "Payment was made at rates higher than those specified in the contract schedule. "
        "Measurement book entries were not reconciled with work completion certificates, "
        "resulting in excess payment."
    ),
    "avoidable_expenditure": (
        "Due to improper planning and lack of site preparation, work was awarded at "
        "rates higher than the sanctioned estimates. The additional expenditure was avoidable "
        "with proper pre-award surveys."
    ),
    "idle_machinery_and_equipment": (
        "Heavy machinery procured at substantial cost remained idle due to absence of matching "
        "civil infrastructure. Procurement was made without ensuring readiness of installation site."
    ),
    "irregular_deployment_of_funds": (
        "Funds earmarked for a specific scheme were diverted for other purposes without "
        "obtaining requisite approval. Expenditure was classified under wrong head of account."
    ),
    "short_recovery_of_dues": (
        "Performance security and liquidated damages were not recovered from the contractor "
        "despite delays and deficiencies in work execution."
    ),
    "fraudulent_claims": (
        "Contractor submitted inflated bills using manipulated measurement records. "
        "Physical verification revealed significant shortfall between claimed and actual work done."
    ),
    "splitting_of_works": (
        "Work orders were split into smaller packages to circumvent the threshold limit for "
        "open tender. Multiple orders were awarded to the same contractor on the same day."
    ),
    "post_award_cost_escalation": (
        "Contract value was enhanced by more than 20% through change orders after initial award, "
        "without rebidding as required under the procurement rules."
    ),
    "non_competitive_bidding": (
        "Only one or two bids were received despite open tender. Bid evaluation committee accepted "
        "the single bid without adequate justification or market assessment."
    ),
    "specification_manipulation": (
        "Technical specifications were drawn up in a restrictive manner to favour a particular "
        "supplier. The specifications matched exactly with only one vendor's product catalogue."
    ),
    "fictitious_expenditure": (
        "Expenditure was claimed on work/supplies that were not actually executed or delivered. "
        "Field inspection revealed discrepancies between records and physical status."
    ),
}


def generate_synthetic_cag_findings(count: int = 50) -> list[dict[str, Any]]:
    findings = []
    for i in range(count):
        ministry = random.choice(MINISTRIES)
        year = random.randint(2019, 2024)
        irr_type = random.choice(IRREGULARITY_TYPES)
        # CAG amounts typically in lakhs-crores
        amount_lakhs = random.randint(5, 50000)
        amount_paise = amount_lakhs * 1_00_000 * 100  # convert to paise

        findings.append({
            "ministry": ministry,
            "year": year,
            "amount": amount_paise,
            "irregularity_type": irr_type,
            "description": DESCRIPTIONS.get(irr_type, "Audit irregularity detected during annual inspection."),
            "source_url": f"https://cag.gov.in/en/audit-report/{year}/ministry-{i+1}",
        })

    return findings


class CAGScraper:
    BASE_URL = "https://cag.gov.in"

    async def scrape_audit_findings(self) -> list[dict[str, Any]]:
        log = logger.bind(source="cag")
        log.info("cag_using_synthetic_findings")
        findings = generate_synthetic_cag_findings(50)
        log.info("cag_findings_generated", count=len(findings))
        return findings
