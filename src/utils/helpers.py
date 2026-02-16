"""
Helper utilities for ReasonableRAG system
"""
import os
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_file_hash(file_path: str) -> str:
    """Generate SHA256 hash of a file for deduplication"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_extension(file_path: str) -> str:
    """Get file extension in lowercase"""
    return os.path.splitext(file_path)[1].lower()


def is_supported_file(file_path: str) -> bool:
    """Check if file format is supported"""
    return get_file_extension(file_path) in config.SUPPORTED_FORMATS


def save_metadata(metadata: Dict[str, Any], file_path: str = config.METADATA_PATH):
    """Save metadata to JSON file"""
    try:
        # Load existing metadata
        existing = load_metadata(file_path)
        existing.update(metadata)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        logger.info(f"Metadata saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")
        raise


def load_metadata(file_path: str = config.METADATA_PATH) -> Dict[str, Any]:
    """Load metadata from JSON file"""
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        return {}


def chunk_text(text: str, chunk_size: int = config.CHUNK_SIZE, 
               overlap: int = config.CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for delimiter in ['. ', '.\n', '! ', '?\n', '? ']:
                last_delim = text[start:end].rfind(delimiter)
                if last_delim != -1:
                    end = start + last_delim + len(delimiter)
                    break
        
        chunk = text[start:end].strip()
        if len(chunk) >= config.MIN_CHUNK_SIZE:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def chunk_text_semantic(text: str, chunk_size: int = config.CHUNK_SIZE) -> List[Dict[str, Any]]:
    """
    Split text into semantic chunks with metadata
    
    Returns chunks with context information
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'timestamp': datetime.now().isoformat()
                })
                chunk_index += 1
            current_chunk = para + "\n\n"
    
    # Add last chunk
    if current_chunk:
        chunks.append({
            'text': current_chunk.strip(),
            'chunk_index': chunk_index,
            'timestamp': datetime.now().isoformat()
        })
    
    return chunks


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    # Remove special characters but keep punctuation
    return text.strip()


def format_document_context(chunks: List[str], metadata: Optional[Dict[str, Any]] = None) -> str:
    """Format retrieved chunks with metadata for LLM context"""
    context_parts = []
    
    if metadata:
        context_parts.append(f"Document Information:")
        for key, value in metadata.items():
            context_parts.append(f"  {key}: {value}")
        context_parts.append("")
    
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[Chunk {i}]")
        context_parts.append(chunk)
        context_parts.append("")
    
    return "\n".join(context_parts)


def estimate_tokens(text: str) -> int:
    """Rough estimation of token count (1 token ≈ 4 characters for English)"""
    return len(text) // 4


def truncate_context(text: str, max_tokens: int = config.MAX_TOKENS) -> str:
    """Truncate text to fit within token limit"""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    
    return text[:max_chars] + "..."


logger.info("Helper utilities loaded successfully")

