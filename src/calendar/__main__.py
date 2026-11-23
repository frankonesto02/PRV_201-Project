"""Run with: python -m src.calendar --year 2026"""
import argparse
import json
from pathlib import Path

from src.calendar.ics_exporter import export_calendar
from src.calendar.table_reader import read_assignments
from src.ingestion import load_all, load_pdf


def main():
    parser = argparse.ArgumentParser(description="Extract syllabus deadlines and export a calendar.")
    parser.add_argument("--input", type=Path, default=Path("data/syllabi"), help="One PDF or a folder of PDFs")
    parser.add_argument("--year", type=int, required=True, help="Year to use for dates without a year")
    parser.add_argument("--timezone", default="America/New_York", help="Timezone for printed deadline times")
    parser.add_argument("--output", type=Path, default=Path("data/calendar/deadlines.ics"))
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"Input does not exist: {args.input}")
    chunks = load_all(args.input) if args.input.is_dir() else load_pdf(args.input)
    items = read_assignments(chunks, year=args.year)
    if not items:
        parser.error("No assignment rows found. Expected table columns: Assignment and Due Date.")
    count = export_calendar(items, args.output, timezone_name=args.timezone)
    review = args.output.with_suffix(".json")
    review.write_text(json.dumps([item.model_dump(mode="json") for item in items], indent=2), encoding="utf-8")
    print(f"Found {len(items)} assignments; exported {count} events to {args.output}")
    print(f"Review extracted dates and source pages in {review}")


if __name__ == "__main__":
    main()
