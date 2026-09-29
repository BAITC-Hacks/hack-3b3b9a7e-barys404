"""One-page Russian PDF briefing built from reviewed institutional aggregates."""

import math
from datetime import date
from html import escape
from importlib.util import find_spec
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _fonts():
    # DejaVu ships with the pinned matplotlib dependency and includes Cyrillic.
    # Locating it without importing pyplot avoids OS font/cache configuration.
    fonts = Path(find_spec("matplotlib").origin).parent / "mpl-data" / "fonts" / "ttf"
    for name, file in [
        ("MedFlow", "DejaVuSans.ttf"),
        ("MedFlowBold", "DejaVuSans-Bold.ttf"),
    ]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(fonts / file)))


def _num(value, digits=1):
    if value is None or not math.isfinite(float(value)):
        return "-"
    return f"{float(value):,.{digits}f}".replace(",", " ").replace(".", ",")


class WaitingBars(Flowable):
    def __init__(self, rows, width):
        Flowable.__init__(self)
        self.rows, self.width = rows, width
        self.height = 20 + len(rows) * 15

    def draw(self):
        canvas = self.canv
        maximum = max([float(r.get("median_wait_days") or 0) for r in self.rows] + [1])
        canvas.setFont("MedFlow", 8)
        canvas.setFillColor(colors.HexColor("#526577"))
        canvas.drawString(0, self.height - 9, "Наблюдаемая медиана ожидания, дни")
        for i, row in enumerate(self.rows):
            y = self.height - 27 - i * 15
            canvas.setFillColor(colors.HexColor("#183044"))
            canvas.drawString(0, y + 2, chr(65 + i))
            value = row.get("median_wait_days")
            if value is not None and math.isfinite(float(value)):
                canvas.setFillColor(colors.HexColor("#e4eeee"))
                canvas.roundRect(20, y, self.width - 80, 10, 3, fill=1, stroke=0)
                canvas.setFillColor(colors.HexColor("#087f8c"))
                bar_width = (self.width - 80) * max(0, float(value)) / maximum
                if bar_width > 0:
                    canvas.roundRect(
                        20, y, bar_width, 10, min(3, bar_width / 2), fill=1, stroke=0
                    )
                canvas.setFillColor(colors.HexColor("#183044"))
                canvas.drawRightString(self.width, y + 1, _num(value))
            else:
                canvas.drawString(20, y + 1, "Недостаточно допустимых исходов")


def build_briefing_pdf(payload, metrics):
    rows = _reviewed_groups(payload)
    _fonts()

    width = A4[0] - 72
    story = _fit_briefing_story(payload, metrics, rows, width)
    output = BytesIO()
    document = _briefing_document(output)
    footer = _briefing_footer(payload)

    document.build([KeepTogether(story)], onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


def _reviewed_groups(payload) -> list[dict]:
    if payload.get("review_status") != "reviewed_for_discussion":
        raise ValueError("Confirm the review before exporting a briefing.")
    rows = payload.get("aggregates", [])
    if not 1 <= len(rows) <= 6:
        raise ValueError("Select one to six comparison groups.")
    return rows


def _text(value) -> str:
    return escape(str(value)).replace("—", "-").replace("–", "-")


def _day(value) -> str:
    return date.fromisoformat(str(value)[:10]).strftime("%d.%m.%Y") if value else "-"


def _fit_briefing_story(payload, metrics, rows, width) -> list:
    for size in (9, 8.5, 8):
        styles = _paragraph_styles(size)
        story = _briefing_story(payload, metrics, rows, width, styles)
        height = sum(
            element.wrap(width, 10000)[1]
            + getattr(element, "spaceBefore", 0)
            + getattr(element, "spaceAfter", 0)
            for element in story
        )
        if height <= A4[1] - 100:
            return story

    raise ValueError(
        "Для одной страницы выберите меньше групп: названия организаций занимают слишком много места."
    )


def _paragraph_styles(size) -> dict:
    body = ParagraphStyle(
        "body",
        fontName="MedFlow",
        fontSize=size,
        leading=size * 1.35,
        textColor=colors.HexColor("#183044"),
    )
    small = ParagraphStyle(
        "small",
        parent=body,
        fontSize=8,
        leading=10.4,
        textColor=colors.HexColor("#526577"),
    )
    heading = ParagraphStyle(
        "heading", parent=body, fontName="MedFlowBold", fontSize=20, leading=25
    )
    section = ParagraphStyle(
        "section",
        parent=body,
        fontName="MedFlowBold",
        fontSize=10,
        leading=14,
        spaceBefore=6,
        spaceAfter=4,
    )
    return {"body": body, "small": small, "heading": heading, "section": section}


def _briefing_story(payload, metrics, rows, width, styles) -> list:
    body, small = styles["body"], styles["small"]
    heading, section = styles["heading"], styles["section"]

    def p(value, style=body):
        return Paragraph(value, style)

    story = _intro_paragraphs(p, payload, rows, width, body, small, heading, section)
    _append_comparison(story, p, rows, width, small)
    _append_model_metrics(story, p, metrics, small, section)
    _append_review_notes(story, p, payload, small, section)
    return story


def _intro_paragraphs(p, payload, rows, width, body, small, heading, section) -> list:
    filters = payload.get("filters", {})
    story = [
        p("MEDFLOW AI", heading),
        p("Сводка для обсуждения со специалистом", section),
        p(
            f"Регистрация: {_day(filters.get('start'))} - {_day(filters.get('end'))}. "
            f"Профиль: {_text(filters.get('bed_profile') or 'все')}. "
            f"Регион происхождения: {_text(filters.get('region_origin_code') or 'все')}.",
            small,
        ),
        Spacer(1, 8),
    ]
    comparison = (
        "Регионы происхождения"
        if payload.get("group_dimension") == "region_origin_code"
        else "Стационары"
    )
    story.append(
        p(
            f"{comparison}: {len(rows)} | Направления: {_num(sum(float(r['referrals']) for r in rows), 0)} | Минимум группы: {payload.get('minimum_group_size', 30)}",
            body,
        )
    )
    story.extend([Spacer(1, 5), WaitingBars(rows, width), Spacer(1, 5)])
    return story


def _append_comparison(story, p, rows, width, small) -> None:
    cells = [
        [
            p("Группа / организация", small),
            p("Напр.", small),
            p("Медиана<br/>дни", small),
            p("P90<br/>дни", small),
            p("Отказы<br/>%", small),
        ]
    ]
    for i, row in enumerate(rows):
        cells.append(
            [
                p(f"{chr(65 + i)}. {_text(row['organization_or_region'])}"),
                p(_num(row.get("referrals"), 0)),
                p(_num(row.get("median_wait_days"))),
                p(_num(row.get("p90_wait_days"))),
                p(_num(row.get("refusal_share_pct"))),
            ]
        )
    table = Table(cells, colWidths=[width - 200, 55, 55, 45, 45], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf4f6")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f7f9fb")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            table,
            Spacer(1, 5),
            p(
                "Ожидание рассчитано по допустимым госпитализациям 0-90 дней. Доля отказов: отказы / (госпитализации + отказы). Пропуск означает недостаточно наблюдений. P90 не является интервалом прогноза.",
                small,
            ),
        ]
    )


def _append_model_metrics(story, p, metrics, small, section) -> None:
    story.append(p("Ошибка сохранённых моделей", section))
    for label, key, unit in [
        ("Ожидание", "waiting", "дня"),
        ("Поток на 7 дней", "forecast", "направления / организацию / день"),
    ]:
        result = metrics.get(key)
        if result:
            version = (
                f" Версия: {_text(result['model_version'])}."
                if result.get("model_version") is not None
                else ""
            )
            story.append(
                p(
                    f"{label}: MAE {_num(result.get('mae'), 2)} {unit}; базовый прогноз {_num(result.get('baseline_mae'), 2)}.{version} Тест: {_text(result.get('period', '-'))}.",
                    small,
                )
            )
        else:
            story.append(p(f"{label}: актуальные метрики недоступны.", small))
    story.append(
        p(
            "Ошибки выше относятся ко всему тестовому набору, не к выбранным группам. Прогноз потока не оценивает занятость коек.",
            small,
        )
    )


def _append_review_notes(story, p, payload, small, section) -> None:
    story.extend(
        [
            p("Вопрос для проверки", section),
            p(
                _text(
                    payload.get(
                        "review_question",
                        "Проверить полноту данных и различия профилей.",
                    )
                )
            ),
            p("Проверка человеком", section),
            p(
                "Аналитик подтвердил просмотр периода, области сравнения и ограничений. Это локальное подтверждение, не формальное согласование. Решение принимает ответственный специалист.",
                small,
            ),
            Spacer(1, 4),
            p(
                "Исторические агрегаты. Сравнение не скорректировано на тяжесть случаев и мощность. Неполная регистрация и незавершённые исходы могут влиять на показатели. Клинические назначения и маршрутизация пациентов не формируются.",
                small,
            ),
        ]
    )


def _briefing_document(output):
    return SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=30,
        bottomMargin=50,
        title="MedFlow AI - сводка для специалиста",
        author="MedFlow AI",
    )


def _briefing_footer(payload):
    def footer(canvas, document):
        canvas.setStrokeColor(colors.HexColor("#dce6ec"))
        canvas.line(36, 39, A4[0] - 36, 39)
        canvas.setFont("MedFlow", 7)
        canvas.setFillColor(colors.HexColor("#526577"))
        version = str(payload.get("source_fingerprint") or "не указана")[:16]
        timestamp = str(payload.get("created_at", ""))[:19].replace("T", " ")
        canvas.drawString(
            36, 26, f"Данные: {version} | Сформировано (UTC): {timestamp}"
        )
        canvas.drawRightString(A4[0] - 36, 26, str(document.page))

    return footer
