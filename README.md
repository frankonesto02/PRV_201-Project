# PRV_201-Project

## Syllabus and Schedule AI Agent
**Course:** PRV201
**Track:** A 
**Team Members and Roles**:
* **Frank Onesto:** Repository scaffolding, base data schemas, and PDF ingestion pipeline
* **Jayden Santana:** Vector database indexing and retrieval pipeline
* **Member 3:** LLM agent (question answering), prompts, and guardrails (optional for now)
* **Member 4:** Citation checker and test suite
* **Dylan Toche:** Table reader that finds due dates and exports them to a calendar file

## Purpose
This tool take college course syllabus PDFs and helps students to:
1. **Find answers to course questions with proof**
2. **Grab assignment due dates**

## How does this relate to our plan?
We used the exact tools we said we would use in our M2 design document:
* **Reading PDFs:** PyMuPDf and pdfplumber
* **Search Database:** ChromaDB
* **AI agent:** Google Gemini API
* **Calendar Output:** exports .ics calendar files

## Changes since M2
* **Calendar output:** `.ics` export instead of the Google Calendar API
* **LLM:** Google Gemini

## Setup
```bash
git clone <repo-url> && cd PRV_201-Project
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # then add your own GEMINI_API_KEY
pytest
```

## Project layout
```
data/syllabi/     10 sample syllabus PDFs
src/models.py     shared data models (SyllabusChunk, AssignmentItem, AgentResponse)
src/ingestion/    PDF loader
src/retrieval/    embeddings + ChromaDB
src/agent/        LLM question answering
src/calendar/     due-date table reader + .ics export
tests/            pytest tests
```

