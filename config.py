"""
Configuration file for ReasonableRAG system
"""
import os

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:14b"  # Primary reasoning model
FAST_LLM_MODEL = "deepseek-r1:7b"  # For quick operations
VISION_MODEL = "llava:7b"  # For image understanding (optional)

# Model Parameters
LLM_TEMPERATURE = 0.1  # Lower for more deterministic responses
LLM_TOP_P = 0.9
LLM_TOP_K = 40
MAX_TOKENS = 2048

# Vector Store Configuration
VECTOR_DB_PATH = "./vector_store"
FAISS_INDEX_PATH = os.path.join(VECTOR_DB_PATH, "faiss_index")
METADATA_PATH = os.path.join(VECTOR_DB_PATH, "metadata.json")
EMBEDDING_DIM = 768  # nomic-embed-text dimension

# Chunking Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
MIN_CHUNK_SIZE = 100  # Minimum chunk size

# Document Processing
UPLOAD_DIR = "./uploaded_documents"
PROCESSED_DIR = "./processed_documents"
SUPPORTED_FORMATS = [
    ".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".xls",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"
]

# RAG Configuration
TOP_K_RETRIEVAL = 5  # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.0  # Minimum similarity score (0.0 = no filtering, use all results)
RERANK_TOP_K = 3  # Number of chunks after reranking

# Messy Data Detection
MESSY_DATA_THRESHOLD = 0.6  # Confidence threshold for messy data detection
MAX_COLUMN_ANALYSIS = 50  # Max columns to analyze for CSV/Excel

# UI Configuration
STREAMLIT_THEME = "dark"
MAX_UPLOAD_SIZE_MB = 200

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "./logs/reasoning_rag.log"

# Create necessary directories
os.makedirs(VECTOR_DB_PATH, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs("./logs", exist_ok=True)

