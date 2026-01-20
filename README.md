# 🧭 Policy Navigator --- Agentic RAG System for Regulations & Health Guidelines

## Overview

**Policy Navigator** is an **Agentic Retrieval-Augmented Generation
(RAG) system** built using **aiXplain**.\
It enables users to **ingest, index, and query** complex **government
regulations, compliance policies, and public health guidelines** from
multiple sources, including:

-   📄 PDF policy documents\
-   📊 CSV datasets\
-   🌐 Public government / health guideline websites

The system is designed to be **interactive**, **incrementally
updatable**, and **source-grounded**, ensuring that answers are always
backed by retrieved documents.

------------------------------------------------------------------------

## ✅ What This Agent Does

The **Policy Navigator Agent**:

-   🔎 Retrieves relevant policy or guideline content from indexed
    sources\
-   🧠 Answers user questions **strictly based on retrieved documents**\
-   📚 Always cites sources (file names or URLs) used in the answer\
-   🚫 Avoids hallucinations when no documents are available\
-   🔁 Allows continuous knowledge base expansion via new uploads\
-   💬 Optionally posts answers to Slack (if Slack tool is configured)

------------------------------------------------------------------------

## 🏗 Architecture (High Level)

User → CLI → Index (PDF / CSV / URLs) → Agent → Answer + Sources

------------------------------------------------------------------------

## ⚙️ Setup Instructions

### Prerequisites

-   Python 3.9+
-   aiXplain API key

``` bash
export AIXPLAIN_API_KEY="your_api_key_here"
```

### Install Dependencies

``` bash
pip install aixplain==0.2.39 pandas requests beautifulsoup4
```

------------------------------------------------------------------------

## 🧠 Models Used

-   **Embeddings**: Snowflake Arctic Embed L\
-   **Document Parsing**: Docling\
-   **LLM**: Configurable via aiXplain console

------------------------------------------------------------------------

## 📚 Knowledge Sources

Supported: - PDF documents - CSV datasets - Public URLs (CDC, WHO, etc.)

Example:
https://www.cdc.gov/water-emergency/safety/guidelines-for-personal-hygiene-during-an-emergency.html

------------------------------------------------------------------------

## 📥 Ingesting Knowledge

Choose Administration Mode: 1. Upload PDF 2. Upload CSV 3. Provide
public URL

Each ingestion **adds to the index**.

------------------------------------------------------------------------

## 🤖 Agent Configuration

-   Loaded by `AGENT_ID`
-   Falls back to `AGENT_NAME`
-   Automatically updates ID when changed

------------------------------------------------------------------------

## 🚀 Run

``` bash
python policy_navigator.py
```

------------------------------------------------------------------------

## 👤 Author

**Mohamed Elwadiny**
