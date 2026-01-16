#!/usr/bin/env python3

from aixplain.factories import FileFactory
import os
from aixplain.factories import (
    AgentFactory,
    IndexFactory,
    FileFactory
)
import logging

logging.getLogger("aixplain").setLevel(logging.WARNING)

# =========================
# CONFIG
# =========================
PROJECT_PREFIX = "PolicyNavigator::"

AGENT_NAME = "Policy Navigator"

EMBEDDING_MODEL_ID = "678a4f8547f687504744960a"  # Snowflake Arctic

from aixplain.factories.tool_factory import ToolFactory

SLACK_TOOL_ID = "686432941223092cb4294d3f"
AGENT_ID = "69683539177e3b074a8a9f31"  # optional
AGENT_INSTRUCTIONS=(
        
    "You are a retrieval-augmented agent answering questions about policies, "
    "regulations, and compliance documents. "

    "Always base your answer strictly on retrieved documents when available. "
    "Do not hallucinate information. "

    "Format every response as follows:\n"
    "1) Answer: a clear, structured explanation\n"
    "2) Sources: a bullet list of document names, URLs, or section identifiers\n\n"

    "If multiple documents are used, list all of them. "
    "If no documents are retrieved, clearly state that no sources were found and "
    "ask the user to ingest documents first. "

    "After answering, if the Slack tool is available, send the full formatted "
    "response to the Slack channel #policy-updates."
)

def get_slack_tool():
    try:
        return ToolFactory.get(SLACK_TOOL_ID)
    except Exception as e:
        print("⚠️ Failed to load Slack tool:", e)
        return None
    

import os
import tempfile
import pandas as pd
# from pypdf import PdfReader, PdfWriter

# ------------------------
# CSV SPLITTER + INGEST
# ------------------------
def ingest_splt_csv(index, max_rows=10000):
    cpath = clean_path(input("Enter CSV file path: "))
    if not os.path.exists(cpath):
        print("❌ File not found.")
        return

    total_rows = 0
    temp_files = []

    try:
        for i, chunk in enumerate(pd.read_csv(cpath, chunksize=max_rows)):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            chunk.to_csv(temp_file.name, index=False)
            temp_files.append(temp_file.name)

            record = index.prepare_record_from_file(temp_file.name)
            index.upsert([record])
            total_rows += len(chunk)
            print(f"✅ Chunk {i+1} ingested ({len(chunk)} rows)")

        print(f"🎉 CSV ingestion completed. Total rows ingested: {total_rows}")

    finally:
        for f in temp_files:
            os.unlink(f)

# ------------------------
# PDF SPLITTER + INGEST
# ------------------------
def ingest_splt_pdf(index, pages_per_chunk=20):
    path = clean_path(input("Enter PDF file path: "))
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    reader = PdfReader(path)
    total_pages = len(reader.pages)
    temp_files = []

    try:
        for i in range(0, total_pages, pages_per_chunk):
            writer = PdfWriter()
            for page in reader.pages[i:i+pages_per_chunk]:
                writer.add_page(page)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            writer.write(temp_file.name)
            temp_files.append(temp_file.name)

            record = index.prepare_record_from_file(temp_file.name)
            index.upsert([record])
            print(f"✅ PDF chunk {i//pages_per_chunk + 1} ingested (pages {i+1}-{min(i+pages_per_chunk, total_pages)})")

        print(f"🎉 PDF ingestion completed. Total pages: {total_pages}")

    finally:
        for f in temp_files:
            os.unlink(f)
    

# =========================
# INDEX UTILITIES
# =========================


def list_indexes():
    all_indexes = IndexFactory.list()["results"]
    return [
        idx for idx in all_indexes
        if idx.name.startswith(PROJECT_PREFIX)
    ]


def create_index():


    name = input("Enter index name (topic): ").strip()
    description = input("Enter index description: ").strip()

    print("📦 Creating index...")
    index = IndexFactory.create(
        name=f"{PROJECT_PREFIX}{name}",
        description=description,
        embedding_model=EMBEDDING_MODEL_ID
    )

    print(f"✅ Index '{name}' created.")
    return index


def select_index():
    indexes = list_indexes()

    if not indexes:
        print("⚠️ No indexes found. Create one first.")
        return None

    print("\nAvailable indexes:")
    for i, idx in enumerate(indexes, start=1):
        print(f"{i}) {idx.name} — {idx.description}")

    choice = input("Select index number: ").strip()

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(indexes):
        print("❌ Invalid selection.")
        return None

    index = IndexFactory.get(indexes[int(choice) - 1].id)
    print(f"📚 Selected index: {index.name}")
    return index
def index_is_empty(index):
    print("Checking if index is empty...")
    try:
        print(f"Index object type: {type(index)}")
        print(f"Index ID: {getattr(index, 'id', 'No ID')}")
        print(f"Index Name: {getattr(index, 'name', 'No Name')}")

        # 1️⃣ Search for one document
        resp = index.search("*", top_k=1)
        #print(f"Raw search response: {resp}")

        # 2️⃣ Extract results safely
        results = resp.data if hasattr(resp, "data") else []
        num_docs = len(results)
        # print(f"🔹 Number of documents in index: {num_docs}")
        if not hasattr(resp, "data") or resp.data is None:
            print("⚠️ Search returned no data attribute.")
            return True

        num_chunks = len(resp.data)
        print(f"🔹 Number of indexed chunks: {num_chunks}")
        return num_docs == 0

    except Exception as e:
        print("⚠️ Failed to check index:", e)
        return True
def get_index_documents(index):
    resp = index.search("*", top_k=1000)  # large enough to sample

    documents = {}

    for r in getattr(resp, "data", []):
        meta = r.get("metadata", {}) or {}

        # Prefer file-based sources
        name = (
            meta.get("file_name")
            or meta.get("source")
            or meta.get("url")
            or "unknown"
        )

        ext = os.path.splitext(name)[1].lower() if "." in name else "url"

        documents.setdefault(ext, set()).add(name)
    # unique_files = {
    #     r["metadata"]["file_name"]
    #     for r in resp.data
    #     if r.get("metadata") and "file_name" in r["metadata"]
    #     }

    # print(f"📄 Total uploaded files: {len(unique_files)}")

        

    
    return documents

# def index_is_empty(index):
#     print("\n🔍 Checking index state...")

#     try:
#         print(f"Index object type: {type(index)}")
#         print(f"Index ID: {index.id}")
#         print(f"Index Name: {index.name}")

#         # Perform a lightweight search to see what's inside
#         resp = index.search("*", limit=1)

#         print("Raw search response type:", type(resp))

#         if not hasattr(resp, "data") or resp.data is None:
#             print("⚠️ Search returned no data attribute.")
#             return True

#         num_chunks = len(resp.data)
#         print(f"🔹 Number of indexed chunks: {num_chunks}")

#         return num_chunks == 0

#     except Exception as e:
#         print("❌ Index check failed:", e)
#         return True



# def index_is_empty(index):
#     print("Checking if index is empty...")
#     try:
#         # print("Index ID: " + index.getid())
#         print(index)
#         info = index.info()
#         print(info.get("num_documents inside the index are ", 0))
#         return info.get("documents", 0) == 0
#     except Exception:
#         return True



# =========================
# INGESTION
# =========================
def clean_path(path: str) -> str:
    return path.strip().strip("'").strip('"')
# def ingest_pdf(index):
#     path = clean_path(input("Enter PDF file path: "))
#     if not os.path.exists(path):
#         print(f"❌ File not found: {path}")
#         return

#     print("📄 Uploading PDF to aiXplain...")

#     try:
#         # 1️⃣ Upload file to aiXplain
#         file_asset = FileFactory.upload(path)
#         print(f"📤 Uploaded file: {file_asset}")

#         # 2️⃣ Index the FILE ASSET (NOT the local path)
#         print("📦 Indexing document (this may take several minutes)...")
#         xx= index.upsert(file_asset.index_id)
#         print(xx)
#         print("✅ PDF successfully indexed and ready for retrieval.")
#         print(index.info())


    # except Exception as e:
    #     print("❌ PDF ingestion failed:")
    #     print(e)

from aixplain.modules.model.record import Record

# def ingest_pdf(index):
#     path = clean_path(input("Enter PDF file path: "))
#     if not os.path.exists(path):
#         print(f"❌ File not found: {path}")
#         return

#     print("📄 Parsing and indexing PDF (this may take a while)...")

#     try:
#         # Step 1: prepare a record from the local PDF
#         record = index.prepare_record_from_file(path)

#         # Step 2: upsert the record into the index
#         response = index.upsert([record])

#         print("✅ PDF successfully indexed and ready for retrieval.")
#         print(f"📄 Added Document ID: {response.data[0]['document_id']}")

#     except Exception as e:
#         print("❌ PDF ingestion failed:")
#         print(e)

# def ingest_pdf(index):
#     path = clean_path(input("Enter PDF file path: "))
#     if not os.path.exists(path):
#         print(f"❌ File not found: {path}")
#         return

#     print("📄 Parsing and indexing PDF (this may take a while)...")

#     try:
#         # Parse + prepare a Record
#         record = index.prepare_record_from_file(path)

#         # Upsert the Record
#         response = index.upsert([record])

#         print("✅ PDF successfully indexed and ready for retrieval.")
#         print(f"📄 Added Document ID: {response.data[0]['document_id']}")

#     except Exception as e:
#         print("❌ PDF ingestion failed:")
#         print(e)
def ingest_pdf(index):
    path = clean_path(input("Enter PDF file path: "))
    
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    print("📄 Parsing and indexing PDF (this may take a while)...")

    try:
        record = index.prepare_record_from_file(path)
        response = index.upsert([record])

        doc_id = response.data[0]['document_id']
        print(f"✅ PDF successfully indexed. Document ID: {doc_id}") 
        # General Debugging
        print(f"Intermediate steps: {response.data.intermediate_steps}")
    
        # 🔹 Immediate search check
        results = index.search("Dietary Guidelines", top_k=3)
        # if results:
        #     print(f"🔹 Search test successful, {len(results)} record(s) retrieved.")
        # else:
        #     print("⚠️ Warning: No documents found on search. Server may need a moment to update.")

        # 🔹 Fetch full index info (server side)
        info = index.info()
        print(f"🔹 Index now has {info['num_documents']} documents.")

    except Exception as e:
        print("❌ PDF ingestion failed:")
        print(e)

def ingest_csv(index):
    cpath = clean_path(input("Enter CSV file path: "))
    if not os.path.exists(cpath):
        print(f"❌ File not found: {cpath}")
        return

    print("📄 Parsing and indexing CSV (this may take a while)...")
    try:
        # Step 1: Prepare record from CSV
        record = index.prepare_record_from_file(cpath)
        
        # Step 2: Upsert the record
        response = index.upsert([record])
        doc_id = response.data[0]["document_id"]
        print(f"✅ CSV successfully indexed. Document ID: {doc_id}")

        # 🔹 Optional: immediate search check
        results = index.search("*", top_k=3)
        print(f"🔹 Test search retrieved {len(getattr(results, 'data', []))} chunk(s).")

        # 🔹 Full index info
        info = index.info()
        print(f"🔹 Index now has {info['num_documents']} documents.")

    except Exception as e:
        print("❌ CSV ingestion failed:")
        print(e)



def ingest_url(index):
    url = input("Enter public URL: ").strip()
    index.upsert(url)
    print("✅ Website ingested.")



def ingest_menu(index):
    while True:
        print("\n--- Ingest Menu ---")
        print("1) PDF")
        print("2) CSV")
        print("3) Website URL")
        print("0) Back")

        choice = input("> ").strip()

        if choice == "1":
            ingest_pdf(index)
        elif choice == "2":
            ingest_csv(index)
        elif choice == "3":
            ingest_url(index)
        elif choice == "0":
            break
        else:
            print("❌ Invalid option.")


# =========================
# AGENT
# =========================

# def get_or_create_agent(index):
#     agents = AgentFactory.list()["results"]

#     for agent in agents:
#         if agent.name == AGENT_NAME:
#             agent = AgentFactory.get(agent.id)
#             agent.tools = [index]
#             return agent

#     print("🤖 Creating agent...")
#     return AgentFactory.create(
#         name=AGENT_NAME,
#         description="Answers questions about government policies using indexed documents",
#         instructions=(
#             "Always answer using retrieved documents when available. "
#             "Cite sources clearly. "
#             "If no documents are available, instruct the user to ingest data first."
#         ),
#         tools=[index]
#     )


def get_or_create_agent(index):
    slack_tool = get_slack_tool()

    if AGENT_ID:
        try:
            print("searching  Agent ID ", AGENT_ID)
            agent = AgentFactory.get(AGENT_ID)
            print(f"Agent found: {agent.name}")
            agent.instructions = AGENT_INSTRUCTIONS
            agent.tools = list({t.id: t for t in ([index, slack_tool] if slack_tool else [index])}.values())
            return agent
        except Exception:
            print("⚠️ Agent ID not found, falling back to name.")

    agents = AgentFactory.list()["results"]
    for a in agents:
        if a.name == AGENT_NAME:
            agent = AgentFactory.get(a.id)
            agent.tools = list({t.id: t for t in ([index, slack_tool] if slack_tool else [index])}.values())
            return agent

    print("🤖 Creating new agent...")
    return AgentFactory.create(
        name=AGENT_NAME,
        description="Answers policy questions using retrieved documents",
        instructions=AGENT_INSTRUCTIONS,
        tools=[index, slack_tool] if slack_tool else [index]
    )

def validate_runtime(agent, index):
    print("==== RUNTIME CHECK ====")
    print(f"Agent   : {agent.name} ({agent.id})")
    print(f"Index   : {index.name} ({index.id})")

    tool_ids = [t.id for t in agent.tools]
    print(f"Index attached : {index.id in tool_ids}")
    print("======================")

    if index.id not in tool_ids:
        raise RuntimeError("Index NOT attached to agent")

def ask_question(agent, index):
    if index_is_empty(index):
        print("⚠️ This index has no documents.")
        print("Please ingest PDFs, CSVs, or URLs first.")
        return

    # Ensure index attached
    if index.id not in [t.id for t in agent.tools]:
        agent.tools.append(index)
        print("🔗 Index attached to agent")
    else:
        print("🔗 Index already attached")

    validate_runtime(agent, index)

    print("\nEntering ASK mode. Type 'back' to return to menu, or 'exit' to quit program.")
    while True:
        question = input("\nAsk your question: ").strip()
        if question.lower() in ["back"]:
            print("🔙 Returning to index menu...")
            break
        if question.lower() in ["exit", "quit"]:
            print("👋 Goodbye.")
            exit(0)

        print("\n⏳ Processing...\n")
        try:
            response = agent.run(question)
            # New API: response.data.output contains the text
            output = getattr(response.data, "output", str(response))
            print("Answer:\n")
            print(output)
            print("-" * 60)
        except Exception as e:
            print("❌ Failed to get answer:", e)


    
    # if index_is_empty(index):
    #     print("⚠️ This index has no documents.")
    #     print("Please ingest PDFs, CSVs, or URLs first.")
    #     return
    # print("index is not empty and documents:")
    # # docs = get_index_documents(index)
    # # for ext, files in docs.items():
    # #         print(f"{ext or 'url'}: {len(files)} documents")
    # print("checking attachement of index to AGENT")
    
    # if index.id not in [t.id for t in agent.tools]:
    #     agent.tools.append(index)
    #     print("🔗 Index attached to agent")
    # else:
    #     print("🔗 Index already attached")

    # validate_runtime(agent, index)
    # question = input("\nAsk your question: ").strip()
    # print("\n⏳ Processing...\n")

    # response = agent.run(question)
    # print("Answer:\n")
    # print(response.data.output)
    # print("-" * 60)


# =========================
# MAIN CLI
# =========================

def index_session(index):
    agent = get_or_create_agent(index)

    while True:
        print(f"\n--- Index: {index.name} ---")
        print("1) Ingest documents")
        print("2) Ask a question")
        print("0) Back to main menu")

        choice = input("> ").strip()

        if choice == "1":
            ingest_menu(index)
        elif choice == "2":
            print("\nEntering ASK mode. Type 'back' to return to menu, or 'exit' to quit program.")
            # while True:
            #     question = input("\nAsk your question: ").strip()
            #     if question.lower() in ["back"]:
            #         print("🔙 Returning to index menu...")
            #         break  # exit ask mode, go back to index menu
            #     if question.lower() in ["exit", "quit"]:
            #         print("👋 Goodbye.")
            #         exit(0)  # exit program entirely

            ask_question(agent, index)  # existing function to handle question

            # while True:
            #     ask_question(agent, index)
            #     response2= input("> ").strip()
            #     if response2.lower() in ["n", "back"]:
            #         break
            #     if response2.lower() in ["n", "exit"]:
            #         exit(0)
        elif choice == "0":
            break
        else:
            print("❌ Invalid option.")


def main():
    import logging

    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("root").setLevel(logging.WARNING)
    print("🚀 Policy Navigator (Multi-Index RAG CLI)")
    logging.getLogger("aixplain").setLevel(logging.WARNING)
    while True:
        print("\n--- Main Menu ---")
        print("1) Create a new index (topic)")
        print("2) List & select existing index")
        print("0) Exit")

        choice = input("> ").strip()

        if choice == "1":
            index = create_index()
            index_session(index)
        elif choice == "2":
            index = select_index()
            if index:
                index_session(index)
        elif choice == "0":
            print("👋 Goodbye.")
            break
        else:
            print("❌ Invalid option.")


if __name__ == "__main__":
    main()

