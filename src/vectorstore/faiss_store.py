"""
FAISS vector store for offline RAG system
"""
import os
import logging
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from src.utils.ollama_client import OllamaClient
import config

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    FAISS-based vector store for semantic search
    """
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or OllamaClient()
        self.index = None
        self.documents = []  # Store actual document chunks
        self.metadata = []   # Store metadata for each chunk
        self.dimension = config.EMBEDDING_DIM
        self.index_path = config.FAISS_INDEX_PATH
        self.docs_path = os.path.join(config.VECTOR_DB_PATH, "documents.pkl")
        self.meta_path = os.path.join(config.VECTOR_DB_PATH, "metadata.pkl")
        
        # Try to load existing index
        self.load()
    
    def create_index(self):
        """Create a new FAISS index"""
        # Use IndexFlatL2 for exact search (good for offline use)
        # For larger datasets, could use IndexIVFFlat
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def add_documents(self, chunks: List[Dict[str, Any]], 
                     batch_size: int = 32) -> int:
        """
        Add document chunks to vector store
        
        Args:
            chunks: List of chunk dictionaries with 'text' and optional metadata
            batch_size: Batch size for embedding generation
        
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        if self.index is None:
            self.create_index()
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings in batches
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.ollama.get_embeddings_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            
            if (i + batch_size) % 100 == 0:
                logger.info(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} embeddings")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype='float32')
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents.extend(texts)
        self.metadata.extend(chunks)
        
        logger.info(f"Added {len(chunks)} chunks to vector store. Total: {len(self.documents)}")
        
        return len(chunks)
    
    def search(self, query: str, top_k: int = config.TOP_K_RETRIEVAL,
               threshold: float = config.SIMILARITY_THRESHOLD) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Similarity threshold (distance threshold)
        
        Returns:
            List of matching chunks with scores
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Generate query embedding
        query_embedding = self.ollama.get_embedding(query)
        query_vector = np.array([query_embedding], dtype='float32')
        
        # Search
        distances, indices = self.index.search(query_vector, top_k)
        
        # Debug logging
        logger.info(f"Search returned distances: {distances[0][:3]}, indices: {indices[0][:3]}")
        logger.info(f"Index total: {self.index.ntotal}, Documents: {len(self.documents)}, Threshold: {threshold}")
        
        # Format results
        results = []
        for idx, (distance, doc_idx) in enumerate(zip(distances[0], indices[0])):
            logger.debug(f"Processing idx={idx}, doc_idx={doc_idx}, distance={distance}")
            
            if doc_idx >= 0 and doc_idx < len(self.documents):  # FAISS returns -1 for invalid indices
                # Convert L2 distance to similarity score
                # Using negative distance so higher score = better match
                similarity = 1 / (1 + float(distance))
                
                logger.debug(f"Similarity: {similarity}, Threshold: {threshold}, Pass: {threshold <= 0 or similarity >= threshold}")
                
                # Filter by threshold (only if threshold > 0)
                if threshold <= 0 or similarity >= threshold:
                    result = {
                        'text': self.documents[doc_idx],
                        'metadata': self.metadata[doc_idx],
                        'score': float(similarity),
                        'distance': float(distance),
                        'rank': idx + 1
                    }
                    results.append(result)
        
        logger.info(f"Found {len(results)} relevant chunks for query (from {top_k} searched)")
        return results
    
    def search_with_filter(self, query: str, filter_fn, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search with custom filter function
        
        Args:
            query: Search query
            filter_fn: Function that takes metadata dict and returns bool
            top_k: Number of results
        
        Returns:
            Filtered search results
        """
        # Get more results initially
        initial_results = self.search(query, top_k=top_k * 3)
        
        # Apply filter
        filtered_results = [r for r in initial_results if filter_fn(r['metadata'])]
        
        return filtered_results[:top_k]
    
    def save(self):
        """Save index and documents to disk"""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save documents
            with open(self.docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            # Save metadata
            with open(self.meta_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"Saved vector store with {len(self.documents)} documents")
        
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    def load(self):
        """Load index and documents from disk"""
        if not os.path.exists(self.index_path):
            logger.info("No existing index found, will create new one")
            return
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load documents
            with open(self.docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            
            # Load metadata
            with open(self.meta_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            logger.info(f"Loaded vector store with {len(self.documents)} documents")
        
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            self.create_index()
    
    def clear(self):
        """Clear all data from vector store"""
        self.create_index()
        self.documents = []
        self.metadata = []
        logger.info("Cleared vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_chunks': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'unique_documents': len(set(m.get('context', {}).get('file_name', '') 
                                       for m in self.metadata))
        }
    
    def delete_by_filename(self, filename: str) -> int:
        """
        Delete all chunks from a specific file
        
        Args:
            filename: Name of file to remove
        
        Returns:
            Number of chunks removed
        """
        # Find indices to keep
        indices_to_keep = []
        new_documents = []
        new_metadata = []
        
        for idx, meta in enumerate(self.metadata):
            file_name = meta.get('context', {}).get('file_name', '')
            if file_name != filename:
                indices_to_keep.append(idx)
                new_documents.append(self.documents[idx])
                new_metadata.append(meta)
        
        removed_count = len(self.documents) - len(new_documents)
        
        if removed_count > 0:
            # Rebuild index with remaining documents
            self.documents = new_documents
            self.metadata = new_metadata
            
            # Recreate index
            self.create_index()
            
            if self.documents:
                # Re-embed all documents (necessary for FAISS)
                logger.info(f"Re-indexing {len(self.documents)} remaining documents...")
                embeddings = self.ollama.get_embeddings_batch(self.documents)
                embeddings_array = np.array(embeddings, dtype='float32')
                self.index.add(embeddings_array)
            
            logger.info(f"Removed {removed_count} chunks from {filename}")
        
        return removed_count


logger.info("FAISS vector store initialized")

