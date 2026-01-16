#!/usr/bin/env python3
"""
rag_agent.py
Reusable Agentic RAG with Aixplain
"""
import requests
import re
from datetime import datetime

import os
import sys
import argparse
from aixplain.factories import AgentFactory, IndexFactory
from aixplain.modules.model.record import Record
from aixplain.modules.model.index_model import Splitter
from aixplain.enums.splitting_options import SplittingOptions
from aixplain.factories.tool_factory import ToolFactory


# -----------------------------
# CONFIG
# -----------------------------
SLACK_TOOL_ID = "686432941223092cb4294d3f"
AGENT_ID = "69669a2d4986b4b80a7d0d1d"   # Policy Navigator Agent
CSV_INDEX_ID = "YOUR_EXISTING_CSV_INDEX_ID"
PDF_INDEX_ID = "YOUR_EXISTING_PDF_INDEX_ID"
WEB_INDEX_ID = "YOUR_EXISTING_WEB_INDEX_ID"
FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"
CSV_FILE = "rows.csv"
PDF_FILE = "policy.pdf"
URL = "https://www.ftc.gov/tips-advice/business-center/privacy-and-security"

DOCLING = "677bee6c6eb56331f9192a91"
FIRECRAWL = "6748d4cff12784b6014324e2"
EMBEDDINGS = "673248d66eb563b2b00f75d1"
LLM = "67be216bd8f6a65d6f74d5e9"  # Claude Sonnet

# -----------------------------
# LOAD AGENT (NO CREATION)
# -----------------------------

def load_agent():
    try:
        agent = AgentFactory.get(AGENT_ID)
        print("✅ Existing agent loaded")
        return agent
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        sys.exit(1)



# -----------------------------
# CUSTOM PYTHON TOOL (CSV)
# -----------------------------
def send_slack_message(slack_tool, channel: str, message: str):
    print("Sending Slack message...")

    try:
        slack_tool.execute({
            "action": "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
            "data": {
                "channel": channel,
                "text": message
            }
        })
        print("✅ Slack message sent")

    except Exception as e:
        print("⚠️ Slack message failed")
        print(e)


# def send_slack_message(slack_tool, channel: str, message: str):
#     print("Sending Slack message...before try")
#     print(slack_tool.id)

#     try:
#         slack_tool.run(
#             action="SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
#             data={
#                 "channel": channel,
#                 "text": message
#             }
#         )
#     except Exception as e:
#         print("Sending Slack message...inside except")
#         print(f"⚠️ Slack message failed: {e}")

def ingest_csv(csv_path):
    try:
        index = IndexFactory.get(CSV_INDEX_ID)

        splitter = Splitter(
            split=True,
            split_by=SplittingOptions.LINE,
            split_length=50,
            split_overlap=5
        )

        records = []
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                records.append(
                    Record(
                        id=f"csv_{i}",
                        value=line,
                        value_type="text",
                        attributes={"source": "csv_dataset"}
                    )
                )

        index.upsert(records, splitter=splitter)
        print(f"✅ CSV ingested: {csv_path}")

    except Exception as e:
        print(f"⚠️ CSV ingestion failed: {e}")

# -----------------------------
# MARKETPLACE TOOLS (PDF / WEB)
# -----------------------------

def ingest_pdf(pdf_path):
    try:
        index = IndexFactory.get(PDF_INDEX_ID)
        index.upsert(pdf_path)  # marketplace PDF parsing
        print(f"✅ PDF ingested: {pdf_path}")
    except Exception as e:
        print(f"⚠️ PDF ingestion failed: {e}")

def ingest_url(url):
    try:
        index = IndexFactory.get(WEB_INDEX_ID)
        index.upsert(url)  # marketplace web scraping
        print(f"✅ URL ingested: {url}")
    except Exception as e:
        print(f"⚠️ URL ingestion failed: {e}")

from aixplain.factories.tool_factory import ToolFactory

SLACK_TOOL_ID = "686432941223092cb4294d3f"
SLACK_TOOL_NAME = "connector-aixplain-slack"

def load_slack_tool(agent):
    """
    Reuse Slack tool if already attached to the agent.
    Attach it only if missing.
    """

    # 1. Check already-attached tools (ModelTool objects)
    for tool in agent.tools:
        if getattr(tool, "name", "") == SLACK_TOOL_NAME:
            print("✅ Slack tool already attached to agent")
            return tool

    # 2. Attach Slack tool only if missing
    try:
        slack_tool = ToolFactory.get(SLACK_TOOL_ID)
        agent.tools.append(slack_tool)
        print("✅ Slack tool attached to agent")
        return slack_tool

    except Exception as e:
        print(f"❌ Failed to load Slack tool: {e}")
        return None

# def load_slack_tool(agent):
#     print("trying to creat ..........Slack tool   ")
#     try:
#         slack_tool = ToolFactory.get(SLACK_TOOL_ID)
#         print("✅ Slack tool created  ")
#         slack_tool.run("test_connection")

#         # Attach tool to existing agent (NO new agent)
#         if slack_tool not in agent.tools:
#             agent.tools.append(slack_tool)
#             agent.save()

#         print("✅ Slack tool attached to agent")
#         return slack_tool

#     except Exception as e:
#         print(f"❌ Failed to load Slack tool: {e}")
#         return None
# -----------------------------
# INTERACTIVE CLI
# -----------------------------
def interactive_loop(agent):
    print("\n=== Policy Navigator Agent (Agentic RAG) ===")
    print("Ask questions. Type 'exit' to quit.\n")

    while True:
        try:
            q = input("Your question: ").strip()
            if q.lower() in ["exit", "quit"]:
                print("Bye 👋")
                break

            # --- AGENTIC ROUTING ---
            if "executive order" in q.lower():
                eo_number = extract_executive_order_number(q)

                if eo_number:
                    answer = check_executive_order_status(eo_number)
                else:
                    answer = "Please specify an Executive Order number."

            else:
                # Default: RAG
                response = agent.run(q)
                answer = response.data.output

            print("\nAnswer:")
            print(answer)
            print("-" * 60)

            # Slack notification (external tool)
            # if slack_tool:
            #     print(slack_tool.name)

            #     send_slack_message(
            #         slack_tool,
            #         channel="#policy-updates",
            #         message=f"*Policy Navigator Update:*\n{answer}"
            #     )

        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")


# def interactive_loop(agent, slack_tool):
#     print("\n=== Policy Navigator Agent (Agentic RAG) ===")
#     print("Ask questions. Type 'exit' to quit.\n")

#     while True:
#         try:
#             q = input("Your question: ").strip()
#             if q.lower() in ["exit", "quit"]:
#                 print("Bye 👋")
#                 break

#             response = agent.run(q)
#             answer = response.data.output

#             print("\nAnswer:")
#             print(answer)
#             print("-" * 60)

#             if slack_tool:
#                 send_slack_message(
#                     slack_tool,
#                     channel="#policy-updates",
#                     message=f"*Policy Navigator Response:*\n{answer}"
#                 )

#         except KeyboardInterrupt:
#             print("\nInterrupted. Exiting.")
#             break
#         except Exception as e:
#             print(f"⚠️ Error: {e}")

# def interactive_loop(agent):
#     print("\n=== Policy Navigator RAG ===")
#     print("Ask questions. Type 'exit' to quit.\n")

#     while True:
#         try:
#             q = input("Your question: ").strip()
#             if q.lower() in ["exit", "quit"]:
#                 print("Bye 👋")
#                 break

#             response = agent.run(q)
#             print("\nAnswer:")
#             print(response.data.output)
#             print("-" * 60)

#         except KeyboardInterrupt:
#             print("\nInterrupted. Exiting.")
#             break
#         except Exception as e:
#             print(f"⚠️ Error: {e}")


# -----------------------------
# CUSTOM TOOL: CHECK EXECUTIVE ORDER STATUS
# -----------------------------

def check_executive_order_status(order_number: str):
    """
    Checks whether an Executive Order is still active using Federal Register API
    """
    params = {
        "conditions[term]": f"Executive Order {order_number}",
        "per_page": 1,
        "order": "newest"
    }

    try:
        r = requests.get(FEDERAL_REGISTER_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not data["results"]:
            return f"No records found for Executive Order {order_number}."

        doc = data["results"][0]
        status = doc.get("document_type", "Unknown")
        date = doc.get("publication_date", "Unknown")

        return (
            f"Executive Order {order_number} is still listed in the Federal Register.\n"
            f"Latest update: {date}\n"
            f"Document type: {status}\n"
            f"Source: Federal Register API"
        )

    except Exception as e:
        return f"Failed to check Executive Order status: {e}"

#----------------
# def check_executive_order_status(order_number: str):
#     """
#     Checks whether an Executive Order is still active using Federal Register API
#     """
#     params = {
#         "conditions[term]": f"Executive Order {order_number}",
#         "per_page": 1,
#         "order": "newest"
#     }

#     try:
#         r = requests.get(FEDERAL_REGISTER_API, params=params, timeout=10)
#         r.raise_for_status()
#         data = r.json()

#         if not data["results"]:
#             return f"No records found for Executive Order {order_number}."

#         doc = data["results"][0]
#         status = doc.get("document_type", "Unknown")
#         date = doc.get("publication_date", "Unknown")

#         return (
#             f"Executive Order {order_number} is still listed in the Federal Register.\n"
#             f"Latest update: {date}\n"
#             f"Document type: {status}\n"
#             f"Source: Federal Register API"
#         )

#     except Exception as e:
#         return f"Failed to check Executive Order status: {e}"

#------------

def extract_executive_order_number(question: str):
    """
    Extract EO number from user question
    """
    match = re.search(r"\b(\d{4,6})\b", question)
    return match.group(1) if match else None

# -----------------------------
# CUSTOM TOOL: CHECK EXECUTIVE ORDER STATUS
FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"

def check_executive_order_status(order_number: str):
    """
    Check Executive Order status using the Federal Register API
    """
    params = {
        "conditions[term]": f"Executive Order {order_number}",
        "per_page": 1,
        "order": "newest"
    }

    try:
        response = requests.get(
            FEDERAL_REGISTER_API,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            return (
                f"No Federal Register records found for "
                f"Executive Order {order_number}."
            )

        doc = data["results"][0]

        title = doc.get("title", "Unknown title")
        pub_date = doc.get("publication_date", "Unknown date")
        doc_type = doc.get("document_type", "Unknown type")
        url = doc.get("html_url", "")

        return (
            f"📜 **Executive Order {order_number} Status**\n"
            f"- Title: {title}\n"
            f"- Document type: {doc_type}\n"
            f"- Latest publication date: {pub_date}\n"
            f"- Source: Federal Register\n"
            f"{url}"
        )

    except Exception as e:
        return f"Failed to check Executive Order {order_number}: {e}"

def format_answer_with_sources(response):
    answer = response.data.output

    refs = getattr(response.data, "references", None)
    if not refs:
        return answer

    sources = []
    for ref in refs:
        src = ref.get("source") or ref.get("attributes", {}).get("source")
        section = ref.get("section") or ref.get("chunk_id")
        if src:
            sources.append(f"- {src} ({section})")

    if not sources:
        return answer

    return (
        f"{answer}\n\n"
        f"Sources:\n" +
        "\n".join(sources)
    )

# -----------------------------
# MAIN
# -----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest-csv", help="Path to CSV dataset")
    parser.add_argument("--ingest-pdf", help="Path to PDF document")
    parser.add_argument("--ingest-url", help="Public website URL")

    agent = load_agent()
    slack_tool = load_slack_tool(agent)

    args = parser.parse_args()
    if args.ingest_csv:
        ingest_csv(args.ingest_csv)

    if args.ingest_pdf:
        ingest_pdf(args.ingest_pdf)

    if args.ingest_url:
        ingest_url(args.ingest_url)

    interactive_loop(agent)

if __name__ == "__main__":
    main()
