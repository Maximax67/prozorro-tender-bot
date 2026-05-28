from html import escape
import re
from typing import Any

PROCUREMENT_METHOD_LABELS: dict[str, str] = {
    "reporting": "Звіт про укладений договір",
    "aboveThreshold": "Відкриті торги",
    "aboveThresholdUA": "Відкриті торги",
    "aboveThresholdUA.defense": "Відкриті торги для потреб оборони",
    "aboveThresholdEU": "Відкриті торги з публікацією на TED",
    "negotiation": "Переговорна процедура",
    "negotiation.quick": "Переговорна процедура (скорочена)",
    "belowThreshold": "Спрощена закупівля",
    "simple.defense": "Спрощена закупівля для потреб оборони",
    "closeFrameworkAgreementUA": "Рамкова угода",
    "priceQuotation": "Запит цінових пропозицій",
}

STATUS_LABELS: dict[str, str] = {
    "active.tendering": "Прийом пропозицій",
    "active.auction": "Аукціон",
    "active.qualification": "Кваліфікація",
    "active.awarded": "Визначення переможця",
    "complete": "Завершено",
    "cancelled": "Скасовано",
    "unsuccessful": "Не відбулось",
    "draft": "Чернетка",
}

CATEGORY_LABELS: dict[str, str] = {
    "goods": "Товари",
    "services": "Послуги",
    "works": "Роботи",
}


def _format_amount(amount: float, vat: bool, currency: str = "UAH") -> str:
    formatted = f"{amount:,.2f}".replace(",", "\u2009").replace(".", ",")
    suffix = " (з ПДВ)" if vat else " (без ПДВ)"
    cur = "грн" if currency == "UAH" else currency
    return f"<code>{formatted}\u00a0{escape(cur)}</code>{suffix}"


def _get_classification_code(tender: dict[str, Any]) -> str:
    items: list[dict[str, Any]] = tender.get("items") or []
    if items:
        cls = items[0].get("classification", {})
        desc: str = cls.get("description", "")
        if desc:
            return desc.lstrip("ДК 021:2015: ")
    general = tender.get("generalClassifier", {})
    desc = general.get("description", "")
    if desc and "не зазначено" not in desc.lower():
        return desc.lstrip("ДК 021:2015: ")
    return "не зазначено"


def _format_classification(value: str) -> str:
    return re.sub(
        r"^([0-9-]+)(\s+—)",
        r"<code>\1</code>\2",
        value,
    )


def _get_title(tender: dict[str, Any]) -> str | None:
    plans: list[dict[str, Any]] = tender.get("plans") or []
    if plans:
        budget: dict[str, Any] | None = plans[0].get("budget")
        if budget:
            description: str | None = budget.get("description")
            if description:
                return description

    lots: list[dict[str, Any]] = tender.get("plans") or []
    if lots:
        title: str | None = lots[0].get("title")
        if title:
            return title

    return None


def _format_items(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""

    total = len(items)
    shown = items[:3]
    header = (
        f"<b>Перші 3 товари (всього {total}):</b>"
        if total > 3
        else f"<b>Товари (всього {total}):</b>"
    )

    lines = [header]
    for i, item in enumerate(shown, 1):
        desc: str = item.get("description", "—")
        qty = item.get("quantity")
        unit_name: str = (item.get("unit") or {}).get("name", "")
        if qty is not None:
            qty_str = f"{qty:g}"
            if unit_name:
                qty_str = f"{qty_str} {unit_name}"
        else:
            qty_str = unit_name or "—"
        lines.append(f"{i}. {escape(desc)} — {escape(qty_str)}")

    return "\n".join(lines)


def format_tender_message(tender: dict[str, Any], has_contract_doc: bool) -> str:
    tender_id: str = tender.get("tenderID", "")
    title: str | None = _get_title(tender)
    description: str = (tender.get("description") or "").strip()
    status_raw: str = tender.get("status", "")
    method_raw: str = tender.get("procurementMethodType", "")
    category_raw: str = tender.get("mainProcurementCategory", "")

    method_label = PROCUREMENT_METHOD_LABELS.get(method_raw, method_raw or "—")
    status_label = STATUS_LABELS.get(status_raw, status_raw or "—")
    category_label = CATEGORY_LABELS.get(category_raw, "")

    value_data: dict[str, Any] = tender.get("value") or {}
    amount: float | None = value_data.get("amount")
    vat: bool = bool(value_data.get("valueAddedTaxIncluded"))
    currency: str = value_data.get("currency", "UAH")

    classification = _get_classification_code(tender)
    items: list[dict[str, Any]] = tender.get("items") or []
    items_str = _format_items(items)

    tender_period: dict[str, Any] | None = tender.get("tenderPeriod")
    end_date_str = ""
    if tender_period and tender_period.get("endDate"):
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(tender_period["endDate"])
            end_date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            end_date_str = tender_period.get("endDate", "")

    lines: list[str] = ["🔔 <b>Нова закупівля</b>", ""]

    lines.append(f"<b>Вид закупівлі:</b> {escape(method_label)}")

    if title:
        lines.append(f"<b>Назва:</b> {escape(title)}")

    lines.append(f"<b>Код:</b> {_format_classification(escape(classification))}")

    if description:
        lines.append(f"<b>Підрозділ:</b> <code>{escape(description)}</code>")

    if category_label:
        lines.append(f"<b>Категорія:</b> {escape(category_label)}")

    if amount is not None:
        lines.append(f"<b>Сума:</b> {_format_amount(amount, vat, currency)}")

    lines.append(f"<b>Статус:</b> {escape(status_label)}")

    if end_date_str:
        lines.append(f"<b>Кінець прийому пропозицій:</b> {escape(end_date_str)}")

    if items_str:
        lines.append("")
        lines.append(items_str)

    lines.append("")

    if has_contract_doc:
        lines.append("<b>📄 Договір:</b> додається файлом")
    else:
        lines.append("<b>📋 Технічні характеристики:</b> додається файлом")

    lines.append("")
    lines.append(f"🔗 https://prozorro.gov.ua/uk/tender/{tender_id}")

    return "\n".join(lines)
