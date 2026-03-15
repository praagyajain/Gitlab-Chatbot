"""Export service for serializing bookmarks to Markdown or PDF bytes."""

import warnings
from datetime import datetime


def bookmarks_to_markdown(bookmarks: list[dict]) -> str:
    """Render bookmarks as a Markdown string.

    Each bookmark has: ## Q: {question}, the answer, and a Sources section.
    Includes a header and timestamp.
    """
    lines = [
        "# My GitLab Handbook Notes",
        f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ]

    for bm in bookmarks:
        question = bm.get("question", "")
        answer = bm.get("answer", "")
        sources = bm.get("sources", [])

        lines.append(f"## Q: {question}")
        lines.append("")
        lines.append(answer)
        lines.append("")

        if sources:
            lines.append("### Sources")
            for src in sources:
                title = src.get("title", src.get("url", ""))
                url = src.get("url", "")
                lines.append(f"- [{title}]({url})")
            lines.append("")

    return "\n".join(lines)


def bookmarks_to_pdf(bookmarks: list[dict]) -> bytes:
    """Render bookmarks as PDF bytes using fpdf2.

    Falls back to UTF-8 encoded Markdown bytes (with a warning prepended)
    if fpdf2 raises any exception.
    """
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "My GitLab Handbook Notes", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(
            0,
            8,
            f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ln=True,
            align="C",
        )
        pdf.ln(6)

        for bm in bookmarks:
            question = bm.get("question", "")
            answer = bm.get("answer", "")
            sources = bm.get("sources", [])

            # Question heading
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 8, f"Q: {question}")
            pdf.ln(2)

            # Answer body
            pdf.set_font("Helvetica", "", 11)
            # Replace non-latin characters to avoid encoding issues
            safe_answer = answer.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 7, safe_answer)
            pdf.ln(2)

            # Sources
            if sources:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 7, "Sources:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for src in sources:
                    title = src.get("title", src.get("url", ""))
                    url = src.get("url", "")
                    safe_line = f"  - {title}: {url}"
                    safe_line = safe_line.encode("latin-1", errors="replace").decode("latin-1")
                    pdf.multi_cell(0, 6, safe_line)

            pdf.ln(4)

        return bytes(pdf.output())

    except Exception as exc:  # noqa: BLE001
        warnings.warn(
            f"PDF generation failed ({exc}); falling back to Markdown bytes.",
            stacklevel=2,
        )
        warning_prefix = (
            "WARNING: PDF generation failed. This is a plain-text Markdown export.\n\n"
        )
        return (warning_prefix + bookmarks_to_markdown(bookmarks)).encode("utf-8")
