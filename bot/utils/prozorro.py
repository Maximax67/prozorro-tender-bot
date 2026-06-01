from typing import Any

import httpx

from app.core.logger import logger
from app.core.settings import settings

PROZORRO_BASE = "https://prozorro.gov.ua/api"
SEARCH_URL = f"{PROZORRO_BASE}/search/tenders"

SUPPORTED_FORMATS: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

TENDER_LIST_PARAMS: dict[str, str] = {
    "buyer[0]": settings.BUYER_ID,
    "sort_by": "tenderID",
    "order": "desc",
}


async def fetch_tenders_list() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(SEARCH_URL, params=TENDER_LIST_PARAMS)
        response.raise_for_status()
        response_data = response.json()
        data: list[dict[str, Any]] = response_data.get("data", [])
        return data


async def fetch_tender_details(tender_id: str) -> dict[str, Any]:
    url = f"{PROZORRO_BASE}/tenders/{tender_id}/details"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data


async def fetch_contract_details(contract_id: str) -> dict[str, Any]:
    url = f"{PROZORRO_BASE}/contracts/{contract_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data


async def download_document(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.error(f"Failed to download document from {url}: {e}")
        return None


def flatten_public_documents(
    public_docs: dict[str, list[dict[str, Any]]] | Any,
) -> list[dict[str, Any]]:
    if not isinstance(public_docs, dict):
        return []

    result: list[dict[str, Any]] = []
    for doc_id, versions in public_docs.items():
        if not isinstance(versions, list) or not versions:
            continue
        latest = max(
            versions,
            key=lambda d: d.get("dateModified", ""),
        )
        result.append(latest)
    return result


def find_addendum3(
    public_docs: dict[str, list[dict[str, Any]]] | Any,
) -> dict[str, Any] | None:
    docs = flatten_public_documents(public_docs)

    # First priority: title contains "Додаток 3"
    for doc in docs:
        title: str = doc.get("title", "")
        fmt: str = doc.get("format", "")
        if "додаток 3" in title.lower() and fmt in SUPPORTED_FORMATS:
            return doc

    # Second priority: title contains "технічн" (технічні характеристики)
    for doc in docs:
        title = doc.get("title", "")
        fmt = doc.get("format", "")
        if "технічн" in title.lower() and fmt in SUPPORTED_FORMATS:
            return doc

    # Third priority: any supported document
    for doc in docs:
        fmt = doc.get("format", "")
        if fmt in SUPPORTED_FORMATS:
            return doc

    return None


def find_contract_document(
    public_docs: dict[str, list[dict[str, Any]]] | Any,
    contract_number: str | None = None,
) -> dict[str, Any] | None:
    docs = flatten_public_documents(public_docs)
    if not docs:
        return None

    contract_num_lower = contract_number.lower() if contract_number else None

    best_doc: dict[str, Any] | None = None
    best_tier = 5

    for doc in docs:
        fmt = doc.get("format", "")
        doc_type = doc.get("documentType", "")
        is_contract_signed = doc_type == "contractSigned"

        # Tier 0 & 1 check
        if contract_num_lower and contract_num_lower in doc.get("title", "").lower():
            if is_contract_signed:
                if fmt == "application/pdf":
                    return doc  # Tier 0: Absolute best, exit immediately!

                if best_tier > 1 and fmt in SUPPORTED_FORMATS:
                    best_doc = doc
                    best_tier = 1
                    continue

        # Tier 2 Check
        if best_tier > 2 and is_contract_signed and fmt in SUPPORTED_FORMATS:
            best_doc = doc
            best_tier = 2
            continue

        # Tier 3 Check
        if best_tier > 3 and fmt == "application/pdf":
            best_doc = doc
            best_tier = 3
            continue

        # Tier 4 Check
        if best_tier > 4 and fmt in SUPPORTED_FORMATS:
            best_doc = doc
            best_tier = 4

    return best_doc
