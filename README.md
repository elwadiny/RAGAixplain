# ARAG_aixplain
Policy Navigator Agent – A Multi-Agent RAG System for Government Regulation Search
# Policy Navigator  
**Agentic RAG System for Government Regulations & Compliance**

---

## 1. What the Agent Does

**Policy Navigator** is an **Agentic Retrieval-Augmented Generation (RAG) system** built using **aiXplain**.  
It enables users to ingest, index, and query complex policy and regulatory documents in a structured, explainable, and citation-aware manner.

### Core Capabilities

- 📚 **Document-grounded question answering**
  - Answers are strictly based on retrieved documents
  - No hallucinated or unsupported responses
- 🗂 **Multi-topic indexing**
  - Users create separate indexes per topic (e.g., *Health Policy*, *Legal Regulations*)
  - Each index persists server-side on aiXplain
- 📄 **Multi-source ingestion**
  - PDF documents
  - CSV datasets
  - Public website URLs
- 🧠 **Semantic retrieval**
  - Uses vector embeddings to retrieve the most relevant content
- 📑 **Citations-first output**
  - Every answer includes explicit source references
- 🔔 **External tool integration**
  - Automatically posts answers to Slack (`#policy-updates`) when available
- 💬 **Interactive CLI**
  - Fully interactive ingestion and querying via terminal

---

## 2. How to Set It Up

### Prerequisites

- Python **3.9+**
- aiXplain account with API access
- Slack workspace (optional, for notifications)

### Installation

```bash
pip install aixplain pandas pypdf
```

### Authentication

Set your aiXplain API key as an environment variable:

```bash
export AIXPLAIN_API_KEY="your_api_key_here"
```

### Run the Application

```bash
python3 policy_navigator.py
```

---

## 3. Dataset / Source Links

This system does **not ship with preloaded data** by design.  
Instead, **users ingest their own sources**, which ensures transparency and contextual relevance.

### Supported Sources

#### Document Upload (User-Provided)
- Government policy PDFs
- Compliance manuals
- Regulatory CSV datasets

#### Public URLs
Examples:
- https://www.federalregister.gov/
- https://www.cdc.gov/
- https://www.who.int/

#### Optional External APIs (Conceptual Extension)
These are **queried live**, not ingested:
- Federal Register API  
  https://www.federalregister.gov/developers/documentation/api/v1
- CourtListener API  
  https://www.courtlistener.com/help/api/rest/

> ⚠️ APIs are **tools**, not documents — they are accessed dynamically by the agent.

---

## 4. Tool Integration Steps

### 4.1 Vector Index (Retrieval Tool)

- Each index is created using:
  - **Snowflake Arctic embedding model**
    ```
    678a4f8547f687504744960a
    ```
- PDFs, CSVs, and URLs are embedded into the same index
- Indexes persist server-side and can be reused across sessions

### 4.2 Slack Tool (External Action Tool)

Slack is integrated using aiXplain’s marketplace connector.

**Tool ID**
```
686432941223092cb4294d3f
```

**Behavior**
- After every successful answer:
  - The agent sends the formatted response to `#policy-updates`
- Slack is optional and fails gracefully if unavailable

---

## 5. Example Inputs / Outputs

### Example 1 — Document-Based Question

**User Action**
```
1) Create index: "Health Policy"
2) Ingest PDF: dietary_guidelines_2024.pdf
3) Ask: "What are the recommended daily sodium limits?"
```

**Agent Output**
```
Answer:
The Dietary Guidelines for Americans recommend limiting sodium intake to less than 2,300 mg per day for adults to reduce the risk of hypertension and cardiovascular disease.

Sources:
- dietary_guidelines_2024.pdf, Section 2.3, Page 45
```

---

### Example 2 — No Documents Ingested

**User Input**
```
Ask: "When does this regulation take effect?"
```

**Agent Output**
```
Answer:
No relevant documents were retrieved to answer this question.

Sources:
None

Please ingest policy documents or URLs before asking questions.
```

---

### Example 3 — Slack Notification

After answering, the same formatted response is automatically posted to:

```
Slack Channel: #policy-updates
```

---

## Summary

This project implements a **fully compliant Agentic RAG system** with:

- Retrieval
- Reasoning
- Tool usage
- Citations
- Persistence
- Human-in-the-loop ingestion

It is intentionally designed to be **transparent, auditable, and extensible**, aligning with real-world policy analysis workflows.
