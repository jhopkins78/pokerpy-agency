import os, json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm

# Paths
SOURCE_DIR = "/Volumes/2TB/PokerPyDrive/knowledge_base/sources"
METADATA_FILE = "/Volumes/2TB/PokerPyDrive/knowledge_base/metadata.json"
VECTOR_STORE_PATH = "/Volumes/2TB/PokerPyDrive/vector_store"

# Load metadata
with open(METADATA_FILE, "r") as f:
    metadata_map = json.load(f)

all_chunks = []

for filename in tqdm(os.listdir(SOURCE_DIR), desc="Processing PDFs"):
    if not filename.endswith(".pdf"):
        continue
    filepath = os.path.join(SOURCE_DIR, filename)
    loader = PyPDFLoader(filepath)
    docs = loader.load()

    category = metadata_map.get(filename, {}).get("category", "uncategorized")
    for doc in docs:
        doc.metadata["source"] = filename
        doc.metadata["category"] = category

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    all_chunks.extend(chunks)

print(f"Total chunks: {len(all_chunks)}")

# Embed + save
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(all_chunks, embeddings)
vectorstore.save_local(VECTOR_STORE_PATH)

print(f"✅ Vector store saved to: {VECTOR_STORE_PATH}")
