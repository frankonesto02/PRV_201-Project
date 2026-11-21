# PRV_201-Project

## Syllabus and Schedule AI Agent
**Course:** PRV201
**Track:** A 
**Team Members and Roles**:
* **Frank Onesto:** Repository scaffolding, base data schemas, and PDF ingestion pipeline.
* **Member 2:** Vector database indexing and retrieval pipeline.
* **Member 3:** LLM agent query maker, prompts, and (guardrails are optional for now)
* **Member 4:** Citation checker and test maker
* **Member 5:** Table reader that finds due dates and export them to calendar file

## Purpose
This tool take college course syllabus PDFs and helps students to:
1. **Find answers to course questions with proof**
2. **Grab assignment due dates**

## How does this relate to our plan?
We used the exact tools we said we would use in our M2 design document:
* **Reading PDFs:** PyMuPDf and pdfplumber
* **Search Database:** ChromaDB
* **AI agent:** Anthropic's Claude API
* **Calendar Output:** exports .ics calendar files

