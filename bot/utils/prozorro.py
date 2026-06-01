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
    contract_num_lower = contract_number.lower() if contract_number else None

    best_doc: dict[str, Any] | None = None
    best_tier = float("inf")  # Lower number means better tier

    for doc in docs:
        fmt = doc.get("format", "")
        is_supported = fmt in SUPPORTED_FORMATS

        doc_type = doc.get("documentType", "")
        title_lower = doc.get("title", "").lower()

        # Tier 1: Contract number matches + type is contractSigned + supported format
        if (
            contract_num_lower
            and contract_num_lower in title_lower
            and doc_type == "contractSigned"
            and is_supported
        ):
            return doc  # Absolute best match, exit early immediately!

        # Tier 2: contractSigned type + supported format
        if best_tier > 2 and doc_type == "contractSigned" and is_supported:
            best_doc = doc
            best_tier = 2
            continue  # Skip lower tier checks for this specific document

        # Tier 3: any PDF
        if best_tier > 3 and fmt == "application/pdf":
            best_doc = doc
            best_tier = 3
            continue

        # Tier 4: any supported format
        if best_tier > 4 and is_supported:
            best_doc = doc
            best_tier = 4

    return best_doc
