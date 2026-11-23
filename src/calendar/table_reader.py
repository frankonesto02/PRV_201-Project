"""Read deadline rows produced by Frank's PDF ingestion module."""
import re
import warnings
from datetime import datetime
from typing import Iterable

from src.models import AssignmentItem, SyllabusChunk


def parse_deadline(value: str, year: int):
    """Parse an explicit date, using the supplied year only if none is printed.

    Numeric slash dates use US month/day order. Relative dates such as
    'next Friday' and 'TBD' are rejected rather than guessed.
    """
    value = re.sub(r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+", "", value.strip(), flags=re.I)
    parts = re.split(r"\s+at\s+", value, maxsplit=1, flags=re.I)
    date_text = parts[0].strip()
    due_time = None
    if len(parts) == 2:
        for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
            try:
                due_time = datetime.strptime(parts[1].strip().upper(), fmt).strftime("%H:%M")
                break
            except ValueError:
                pass
        if due_time is None:
            raise ValueError(f"Unsupported deadline time: {parts[1]}")

    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_text, fmt).date(), due_time
        except ValueError:
            pass
    for fmt in ("%b %d %Y", "%B %d %Y", "%m/%d %Y"):
        try:
            return datetime.strptime(f"{date_text} {year}", fmt).date(), due_time
        except ValueError:
            pass
    raise ValueError(f"Unsupported or invalid deadline: {value}")


def read_assignments(chunks: Iterable[SyllabusChunk], *, year: int) -> list[AssignmentItem]:
    """Extract exact assignment/deadline rows; ignore grading and weekly tables.

    Invalid deadlines produce a warning and remain undated for review.
    Repeated rows are deduplicated within a source PDF.
    """
    if not 1 <= year <= 9999:
        raise ValueError("year must be between 1 and 9999")
    items = []
    seen = set()
    for chunk in chunks:
        if chunk.chunk_type != "table":
            continue
        for row in chunk.text.splitlines():
            fields = {}
            for cell in row.split(" | "):
                key, separator, value = cell.partition(":")
                if separator:
                    fields[key.strip().lower()] = value.strip()
            title = fields.get("assignment")
            if not title or "due date" not in fields:
                continue
            try:
                due_date, due_time = parse_deadline(fields["due date"], year)
            except ValueError as exc:
                warnings.warn(f"{chunk.source_file}, page {chunk.page_number}, {title}: {exc}", UserWarning)
                due_date, due_time = None, None
            weight = fields.get("weight", "")
            match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", weight)
            item = AssignmentItem(
                title=title, course_code=chunk.course_code, due_date=due_date,
                due_time=due_time, point_weight=float(match[1]) if match else None,
                page_reference=chunk.page_number,
            )
            key = (chunk.source_file, item.course_code, title, due_date, due_time)
            if key not in seen:
                seen.add(key)
                items.append(item)
    return items
