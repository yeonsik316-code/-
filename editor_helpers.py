"""글 작성 서식 도구 및 가독성 표시."""
import re
from html import escape

SIZE_MAP = {
    "작게": "14px",
    "보통": "16px",
    "크게": "20px",
    "제목": "24px",
}

COLOR_MAP = {
    "검정": "#1e293b",
    "파란": "#2563eb",
    "빨간": "#dc2626",
}


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&nbsp;", " ")
    return text.strip()


def count_chars(html: str) -> dict:
    plain = strip_html(html)
    no_space = plain.replace(" ", "").replace("\n", "")
    return {
        "total": len(plain),
        "no_space": len(no_space),
        "lines": plain.count("\n") + 1 if plain else 0,
    }


def readability_hint(counts: dict) -> tuple[str, str]:
    total = counts["total"]
    if total == 0:
        return "info", "내용을 입력하면 글자 수와 가독성 가이드가 표시됩니다."
    if total < 50:
        return "warning", "내용이 짧습니다. 현장에서 필요한 조치·연락처·참고사항을 보완해 주세요."
    if total > 3000:
        return "warning", "내용이 매우 깁니다. 소제목·목록으로 나누면 모바일에서 읽기 쉽습니다."
    if counts["lines"] > 25:
        return "warning", "줄이 많습니다. 빈 줄로 문단을 나누어 주세요."
    return "success", "적절한 길이입니다. 문단 사이 빈 줄을 유지하면 가독성이 좋습니다."


def wrap_selection(text: str, selection: str, open_tag: str, close_tag: str) -> str:
    selection = selection.strip()
    if not selection:
        return text + open_tag + "텍스트" + close_tag
    if selection in text:
        return text.replace(selection, open_tag + selection + close_tag, 1)
    return text + open_tag + selection + close_tag


def apply_bold(content: str, selection: str) -> str:
    return wrap_selection(content, selection, "<strong>", "</strong>")


def apply_size(content: str, selection: str, size_label: str) -> str:
    size = SIZE_MAP.get(size_label, "16px")
    tag_open = f'<span style="font-size:{size};">'
    return wrap_selection(content, selection, tag_open, "</span>")


def apply_color(content: str, selection: str, color_label: str) -> str:
    color = COLOR_MAP.get(color_label, "#1e293b")
    tag_open = f'<span style="color:{color};">'
    return wrap_selection(content, selection, tag_open, "</span>")


def render_preview(html: str) -> str:
    if not html.strip():
        return "<p style='color:#94a3b8;'>미리보기가 여기에 표시됩니다.</p>"
    return f"<div style='line-height:1.7;font-size:16px;'>{html}</div>"
