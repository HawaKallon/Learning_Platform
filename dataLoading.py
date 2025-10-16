import os
import sys
import io
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Clean up environment to suppress warnings/logs
sys.stderr = io.StringIO()

os.environ["USER_AGENT"] = "Mozilla/5.0 (compatible; YourBot/1.0)"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
import glob
import warnings
import logging

# ----------------------------
# CLEAN TERMINAL OUTPUT
# ----------------------------
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("PyPDF2").setLevel(logging.ERROR)

# ----------------------------
# CONFIGURATION
# ----------------------------
PDF_FILE_PATH = "SSS-Syllabus-Mathematics-for-STEAMM.pdf" 
VECTORSTORE_PATH = "SSS_Curriculum_faiss" 
METADATA_FILE = "vectorstore_metadata.json"

# ----------------------------
# METADATA MANAGEMENT
# ----------------------------
def get_file_hash(file_path):
    """Generate hash of the syllabus PDF for change detection"""
    hash_md5 = hashlib.md5()
    
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    
    return hash_md5.hexdigest()

def get_metadata():
    """Load or initialize metadata for the vectorstore"""
    if Path(METADATA_FILE).exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(files_hash, num_documents, num_chunks):
    """Save metadata after a successful build"""
    metadata = {
        "file_hash": files_hash,
        "num_documents": num_documents,
        "num_chunks": num_chunks,
        "last_build": datetime.now().isoformat()
    }
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)
    return metadata

def should_rebuild_vectorstore():
    """Check if the vectorstore exists and if the source file has changed."""
    if not Path(VECTORSTORE_PATH).exists():
        print(f"💡 Vectorstore folder missing at '{VECTORSTORE_PATH}'. Rebuilding.")
        return True
    
    current_hash = get_file_hash(PDF_FILE_PATH)
    metadata = get_metadata()
    
    if metadata.get("file_hash") != current_hash:
        print("💡 File hash mismatch. Rebuilding vectorstore.")
        return True
    
    return False

# ----------------------------
# CORE RAG FUNCTIONS
# ----------------------------

def create_embeddings():
    """Initialize the HuggingFace Embeddings model."""
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return embeddings

def build_vectorstore():
    """Load the PDF, chunk it, and build the FAISS vectorstore."""
    print("\n" + "=" * 80)
    print("🧠 BUILDING NEW CURRICULUM VECTORSTORE")
    print("=" * 80)
    vectorstore = None # Initialize vectorstore to None

    if not Path(PDF_FILE_PATH).exists():
        print(f"❌ Error: Syllabus file not found at '{PDF_FILE_PATH}'")
        return None, None
        
    try:
        # 1. Load documents
        loader = PyPDFLoader(PDF_FILE_PATH)
        documents = loader.load()
        print(f"📄 Loaded 1 document ({len(documents)} pages)")

        # 2. Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        text_chunks = text_splitter.split_documents(documents)
        print(f"✂️ Split into {len(text_chunks)} chunks for RAG")

        # 3. Create embeddings and vectorstore
        embeddings = create_embeddings()
        vectorstore = FAISS.from_documents(text_chunks, embeddings)
        print("✅ Embeddings created.")

        # 4. Save and return - ADDED EXPLICIT DIRECTORY CREATION AND ERROR HANDING
        Path(VECTORSTORE_PATH).mkdir(exist_ok=True) 
        
        try:
            vectorstore.save_local(VECTORSTORE_PATH)
            print(f"💾 Vectorstore saved to {VECTORSTORE_PATH}")
            
            # Save metadata only if save_local succeeds
            files_hash = get_file_hash(PDF_FILE_PATH)
            metadata = save_metadata(files_hash, len(documents), len(text_chunks))
            print(f"📝 Metadata saved: {metadata['num_chunks']} chunks, built at {metadata['last_build']}")

        except Exception as save_e:
            print(f"❌ CRITICAL SAVE ERROR: Failed to write files to disk. Check directory permissions.")
            print(f"Error details: {save_e}")
            vectorstore = None # Ensure we return failure status
            
    except Exception as general_e:
        print(f"❌ General Error during build process: {general_e}")


    print("=" * 80 + "\n")
    return vectorstore, embeddings


def load_vectorstore():
    """Load existing vectorstore from disk"""
    print("\n" + "=" * 80)
    print("⚡ LOADING CACHED CURRICULUM VECTORSTORE")
    print("=" * 80)
    
    # Check that the necessary files exist before attempting to load
    if not (Path(VECTORSTORE_PATH) / "index.faiss").exists():
        print(f"⚠️  Cached index file missing in {VECTORSTORE_PATH}. Forcing rebuild.")
        return build_vectorstore()
        
    try:
        embeddings = create_embeddings()
        vectorstore = FAISS.load_local(
            VECTORSTORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

        metadata = get_metadata()
        if metadata:
            print(f"📊 Loaded vectorstore with {metadata.get('num_chunks', 'N/A')} chunks")
            print(f"📅 Last built: {metadata.get('last_build', 'N/A')}")

        print("✅ Vectorstore loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading vectorstore: {e}. Attempting rebuild.")
        return build_vectorstore()

    print("=" * 80 + "\n")
    return vectorstore, embeddings


# ----------------------------
# MAIN INITIALIZATION
# ----------------------------
def initialize_vectorstore(force_rebuild=False):
    """Initialize vectorstore with caching"""
    if force_rebuild or should_rebuild_vectorstore():
        return build_vectorstore()
    else:
        return load_vectorstore()


# Initialize on import
print("DEBUG: Initializing vectorstore...")
vectorstore, embeddings = initialize_vectorstore()
print(f"DEBUG: Vectorstore initialization result: {'SUCCESS' if vectorstore else 'FAILURE'}")

# ----------------------------
# UTILITY FUNCTIONS
# ----------------------------
def check_status():
    """Return status of the vectorstore"""
    metadata = get_metadata()
    return {
        "status": "ready" if vectorstore else "error",
        "last_build": metadata.get("last_build"),
        "num_chunks": metadata.get("num_chunks"),
        "source_file": PDF_FILE_PATH
    }