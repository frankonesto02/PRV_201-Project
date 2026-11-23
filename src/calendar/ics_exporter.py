"""Export AssignmentItem objects to a portable iCalendar (.ics) file."""
import warnings
from datetime import datetime, time, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from src.models import AssignmentItem


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def _fold(line: str) -> str:
    """Fold content lines at 75 UTF-8 octets without splitting characters."""
    lines, current = [], ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            lines.append(current)
            current = " "
        current += char
    return "\r\n".join(lines + [current])


def export_calendar(assignments: Iterable[AssignmentItem], output_path, *, timezone_name="America/New_York") -> int:
    """Write dated assignments and return the number of events exported.

    Times are interpreted in timezone_name and stored in UTC. Date-only
    deadlines become all-day events. Undated items are skipped with a warning.
    """
    zone = ZoneInfo(timezone_name)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//PRV201//Syllabus Calendar//EN", "CALSCALE:GREGORIAN"]
    count = 0
    for item in assignments:
        if item.due_date is None:
            warnings.warn(f"Skipped undated assignment: {item.course_code}: {item.title}", UserWarning)
            continue
        identity = f"{item.course_code}|{item.title}|{item.due_date}|{item.due_time}"
        event = ["BEGIN:VEVENT", f"UID:{sha256(identity.encode()).hexdigest()}@prv201", f"DTSTAMP:{stamp}"]
        if item.due_time:
            local = datetime.combine(item.due_date, time.fromisoformat(item.due_time))
            aware = local.replace(tzinfo=zone)
            if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != local:
                raise ValueError(f"Nonexistent local time for {item.title}: {local}")
            if aware.utcoffset() != local.replace(tzinfo=zone, fold=1).utcoffset():
                raise ValueError(f"Ambiguous local time for {item.title}: {local}")
            event.append(f"DTSTART:{aware.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
        else:
            event.append(f"DTSTART;VALUE=DATE:{item.due_date.strftime('%Y%m%d')}")
        description = f"Syllabus page {item.page_reference}"
        if item.point_weight is not None:
            description += f"; weight: {item.point_weight:g}%"
        event.extend([f"SUMMARY:{_escape(item.course_code + ': ' + item.title)}", f"DESCRIPTION:{_escape(description)}", "END:VEVENT"])
        lines.extend(event)
        count += 1
    lines.append("END:VCALENDAR")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\r\n".join(_fold(line) for line in lines) + "\r\n").encode("utf-8"))
    return count
