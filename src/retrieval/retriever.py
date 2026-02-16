"""
Retrieval module for RAG system
"""
import logging
from typing import List, Dict, Any, Optional
from src.vectorstore.faiss_store import FAISSVectorStore
from src.utils.ollama_client import OllamaClient
import config

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant context from vector store
    """
    
    def __init__(self, vector_store: Optional[FAISSVectorStore] = None,
                 ollama_client: Optional[OllamaClient] = None):
        self.vector_store = vector_store or FAISSVectorStore()
        self.ollama = ollama_client or OllamaClient()
    
    def retrieve(self, query: str, top_k: int = config.TOP_K_RETRIEVAL) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
        
        Returns:
            List of relevant chunks with metadata
        """
        logger.info(f"Retrieving context for query: {query[:100]}...")
        
        # Retrieve from vector store
        results = self.vector_store.search(query, top_k=top_k)
        
        return results
    
    def retrieve_with_rerank(self, query: str, 
                            top_k: int = config.TOP_K_RETRIEVAL,
                            rerank_top_k: int = config.RERANK_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank results using LLM
        
        Args:
            query: User query
            top_k: Initial retrieval count
            rerank_top_k: Final count after reranking
        
        Returns:
            Reranked list of chunks
        """
        # Initial retrieval
        initial_results = self.retrieve(query, top_k=top_k)
        
        if len(initial_results) <= rerank_top_k:
            return initial_results
        
        # Rerank using LLM
        reranked = self._rerank_with_llm(query, initial_results, rerank_top_k)
        
        return reranked
    
    def _rerank_with_llm(self, query: str, chunks: List[Dict[str, Any]], 
                         top_k: int) -> List[Dict[str, Any]]:
        """
        Use LLM to rerank chunks based on relevance
        
        This provides more accurate ranking than pure vector similarity
        """
        logger.info(f"Reranking {len(chunks)} chunks to top {top_k}")
        
        # For efficiency, use a simple scoring approach
        # In production, you might use a dedicated reranking model
        
        scored_chunks = []
        for chunk in chunks:
            # Create a simple relevance prompt
            prompt = f"""On a scale of 0-10, how relevant is this text to answering the question?
Question: {query}

Text: {chunk['text'][:500]}

Relevance score (0-10):"""
            
            try:
                response = self.ollama.generate(prompt, model=config.FAST_LLM_MODEL,
                                              temperature=0.1)
                # Extract numeric score
                score_str = ''.join(filter(str.isdigit, response[:10]))
                score = int(score_str) if score_str else chunk['score'] * 10
            except:
                score = chunk['score'] * 10
            
            chunk['rerank_score'] = score
            scored_chunks.append(chunk)
        
        # Sort by rerank score
        scored_chunks.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return scored_chunks[:top_k]
    
    def retrieve_hybrid(self, query: str, keywords: List[str] = None,
                       top_k: int = config.TOP_K_RETRIEVAL) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval: semantic + keyword matching
        
        Args:
            query: Main query
            keywords: Additional keywords to boost
            top_k: Number of results
        
        Returns:
            Combined results
        """
        # Semantic retrieval
        semantic_results = self.retrieve(query, top_k=top_k)
        
        if not keywords:
            return semantic_results
        
        # Boost scores for chunks containing keywords
        for result in semantic_results:
            text_lower = result['text'].lower()
            keyword_matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            
            # Boost score based on keyword matches
            if keyword_matches > 0:
                result['score'] = result['score'] * (1 + 0.1 * keyword_matches)
                result['keyword_matches'] = keyword_matches
        
        # Re-sort by updated scores
        semantic_results.sort(key=lambda x: x['score'], reverse=True)
        
        return semantic_results[:top_k]


logger.info("Retriever initialized")

