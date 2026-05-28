from io import BytesIO
from typing import Any

from aiogram.types import BufferedInputFile

from app.core.logger import logger
from app.core.settings import settings
from bot.instance import bot
from bot.utils.formatter import format_tender_message
from bot.utils.prozorro import (
    SUPPORTED_FORMATS,
    download_document,
    fetch_contract_details,
    fetch_tender_details,
    fetch_tenders_list,
    find_addendum3,
    find_contract_document,
)
from bot.utils.upstash import get_last_tender_id, set_last_tender_id

MAX_FIRST_RUN_TENDERS = 5


async def _find_and_download_document(
    tender: dict[str, Any],
) -> tuple[bytes | None, str, bool]:
    """
    Returns (file_bytes, filename, is_contract).
    Tries contract documents first, then falls back to Додаток 3.
    """
    contracts: list[dict[str, Any]] = tender.get("contracts") or []
    active_contracts = [c for c in contracts if c.get("status") == "active"]

    for contract in active_contracts:
        contract_id: str = contract.get("contractID", "")
        if not contract_id:
            continue

        try:
            contract_details = await fetch_contract_details(contract_id)
            pub_docs = contract_details.get("publicDocuments", {})
            doc = find_contract_document(pub_docs)
            if doc:
                url: str = doc.get("url", "")
                title: str = doc.get("title", "contract")
                fmt: str = doc.get("format", "")
                ext = SUPPORTED_FORMATS.get(fmt, "")
                filename = title if "." in title else f"{title}{ext}"
                data = await download_document(url)
                if data:
                    return data, filename, True
        except Exception as e:
            logger.error(f"Failed to fetch contract {contract_id}: {e}")
            continue

    # Fallback to Додаток 3 from tender's own publicDocuments
    pub_docs = tender.get("publicDocuments", {})
    doc = find_addendum3(pub_docs)
    if doc:
        url = doc.get("url", "")
        title = doc.get("title", "addendum3")
        fmt = doc.get("format", "")
        ext = SUPPORTED_FORMATS.get(fmt, "")
        filename = title if "." in title else f"{title}{ext}"
        data = await download_document(url)
        if data:
            return data, filename, False

    return None, "", False


async def _send_tender_notification(tender: dict[str, Any]) -> None:
    tender_id: str = tender.get("tenderID", "")
    file_bytes, filename, is_contract = await _find_and_download_document(tender)

    has_doc = file_bytes is not None
    text = format_tender_message(tender, is_contract and has_doc)

    if has_doc and file_bytes is not None:
        try:
            document = BufferedInputFile(
                file=BytesIO(file_bytes).read(),
                filename=filename,
            )
            await bot.send_document(
                chat_id=settings.CHAT_ID,
                message_thread_id=settings.MESSAGE_THREAD_ID,
                document=document,
                caption=text,
            )
            return
        except Exception as e:
            logger.error(f"Failed to send document for {tender_id}: {e}")
            # Fall through to sending text-only with error note
            text += f"\n\n⚠️ <i>Не вдалось надіслати файл: {e}</i>"

    await bot.send_message(
        chat_id=settings.CHAT_ID,
        message_thread_id=settings.MESSAGE_THREAD_ID,
        text=text,
    )

    if not has_doc:
        await bot.send_message(
            chat_id=settings.CHAT_ID,
            message_thread_id=settings.MESSAGE_THREAD_ID,
            text=f"⚠️ <i>Для тендера {tender_id} не знайдено документів для завантаження</i>",
        )


async def check_new_tenders() -> int:
    tenders = await fetch_tenders_list()
    if not tenders:
        logger.info("No tenders returned from API")
        return 0

    last_id = await get_last_tender_id()

    if last_id is None:
        new_tenders = tenders[MAX_FIRST_RUN_TENDERS:]
        logger.info(f"First run: processing last {len(new_tenders)} tenders")
    else:
        new_tenders = [t for t in tenders if t.get("tenderID", "") > last_id]
        logger.info(f"Found {len(new_tenders)} new tenders since {last_id}")

    if not new_tenders:
        return 0

    # Process oldest first
    new_tenders.sort(key=lambda t: t.get("tenderID", ""))

    processed = 0
    for summary in new_tenders:
        tender_id: str = summary.get("tenderID", "")
        if not tender_id:
            continue

        try:
            logger.info(f"Processing tender {tender_id}")
            details = await fetch_tender_details(tender_id)
            await _send_tender_notification(details)
            await set_last_tender_id(tender_id)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to process tender {tender_id}: {e}")
            try:
                await bot.send_message(
                    chat_id=settings.CHAT_ID,
                    message_thread_id=settings.MESSAGE_THREAD_ID,
                    text=f"❌ Помилка при обробці тендера <code>{tender_id}</code>:\n<code>{e}</code>",
                )
            except Exception:
                pass

    return processed
