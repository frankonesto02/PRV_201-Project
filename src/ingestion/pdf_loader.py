"""Load syllabus PDFs and turn them into SyllabusChunk objects.
PyMuPDF reads the text. pdfplumber finds the tables, because
PyMuPDF flattens tables into messy text.
"""
import json
import re
from pathlib import Path
import pdfplumber
import pymupdf
from src.models import SyllabusChunk

MAX_CHARS = 800         # rough maximum size of a text chunk
EDGE = 0.07
SMALL_WORDS = {"and", "of", "the", "for", "to", "in", "a", "on", "or"}

def find_course_code(first_page_text, filename):
    """Look for something like 'CS 101' or 'MA-221' on page 1, then in the filename."""
    pattern = r"\b([A-Z]{2,4})[ -]?(\d{3})\b"
    stem = Path(filename).stem.upper().replace("_", " ")
    for source in (first_page_text, stem):
        match = re.search(pattern, source)
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return "UNKNOWN"

def looks_like_heading(line):
    """Guess whether a one-line block is a section heading."""
    line = line.strip()
    if not 3 <= len(line) <= 60:
        return False
    if line.endswith((".", ",")) or ":" in line or "|" in line:
        return False
    if line.isupper():
        return True
    words = line.split()
    if len(words) > 6:
        return False
    return all(w[0].isupper() or w.lower() in SMALL_WORDS for w in words if w[0].isalpha())

def get_tables(pdf_path):
    """Return {page_number: [(bbox, rows), ...]} for every table pdfplumber finds."""
    found = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.find_tables():
                rows = [[(cell or "").replace("\n", " ").strip() for cell in row]
                        for row in table.extract()]
                if len(rows) >= 2 and len(rows[0]) >= 2:   # ignore 1-row "tables"
                    found.setdefault(page_number, []).append((table.bbox, rows))
    return found

def table_to_text(rows):
    """Turn each row into 'Header: value | Header: value' so a row makes sense by itself."""
    header = rows[0]
    lines = []
    for row in rows[1:]:
        cells = [f"{h}: {v}" for h, v in zip(header, row) if v]
        if cells:
            lines.append(" | ".join(cells))
    return "\n".join(lines)

def inside(block, bbox):
    """Is the middle of a text block inside a table's bounding box?"""
    x_mid = (block[0] + block[2]) / 2
    y_mid = (block[1] + block[3]) / 2
    return bbox[0] <= x_mid <= bbox[2] and bbox[1] <= y_mid <= bbox[3]

def load_pdf(pdf_path):
    """Read one PDF and return a list of SyllabusChunk objects."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"No such file: {pdf_path}")

    tables = get_tables(pdf_path)
    chunks = []
    doc = pymupdf.open(pdf_path)
    course_code = find_course_code(doc[0].get_text(), pdf_path.name)
    section = "Front Matter"      # used until we hit the first heading

    def add(text, page_number, section_title, chunk_type="text"):
        chunks.append(SyllabusChunk(
            text=text, course_code=course_code, section_title=section_title,
            page_number=page_number, source_file=pdf_path.name, chunk_type=chunk_type))

    for page_number, page in enumerate(doc, start=1):
        page_tables = tables.get(page_number, [])
        height = page.rect.height
        section_at_start = section    # a table at the top of a page continues this section
        headings = []             # (y position, title) so tables can be labeled
        pieces = []               # paragraphs waiting to become a chunk
        piece_section = section

        def flush():
            if pieces:
                add("\n".join(pieces), page_number, piece_section)
                pieces.clear()

        # blocks look like (x0, y0, x1, y1, text, block_no, block_type)
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text = block[:5]
            text = text.strip()
            if block[6] != 0 or not text:
                continue
            if y1 < EDGE * height or y0 > (1 - EDGE) * height:   # header/footer
                continue
            if any(inside(block, bbox) for bbox, _ in page_tables):  # handled as a table
                continue

            if "\n" not in text and looks_like_heading(text):
                flush()
                section = piece_section = text
                headings.append((y1, text))
                continue

            paragraph = re.sub(r"\s*\n\s*(?![•\-\d])", " ", text)
            if pieces and sum(len(p) for p in pieces) + len(paragraph) > MAX_CHARS:
                flush()
            pieces.append(paragraph)
        flush()

        for bbox, rows in page_tables:
            above = [title for y, title in headings if y <= bbox[1] + 2]
            add(table_to_text(rows), page_number, above[-1] if above else section_at_start, "table")

    doc.close()
    return chunks

def load_all(folder="data/syllabi"):
    """Load every PDF in a folder (sorted by name)."""
    chunks = []
    for pdf_path in sorted(Path(folder).glob("*.pdf")):
        chunks.extend(load_pdf(pdf_path))
    return chunks

if __name__ == "__main__":
    all_chunks = load_all()
    out = Path("data/chunks.json")
    out.write_text(json.dumps([c.model_dump() for c in all_chunks], indent=2))
    print(f"Wrote {len(all_chunks)} chunks to {out}")
