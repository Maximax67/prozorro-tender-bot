from fastapi import APIRouter, Header, HTTPException

from app.core.logger import logger
from app.core.settings import settings
from bot.utils.tender_checker import check_new_tenders

router = APIRouter(prefix="/cron", tags=["cron"])


@router.post("/check-tenders")
@router.get("/check-tenders")
async def cron_check_tenders(
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    expected = f"Bearer {settings.CRON_SECRET.get_secret_value()}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        count = await check_new_tenders()
        logger.info(f"Cron job processed {count} new tenders")
        return {"status": "ok", "processed": count}
    except Exception as e:
        logger.error(f"Cron job failed: {e}")
        return {"status": "error", "detail": str(e)}
