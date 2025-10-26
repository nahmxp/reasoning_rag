"""
Generation module for RAG system
Generates educational responses using retrieved context
"""
import logging
from typing import List, Dict, Any, Optional, Iterator
from src.utils.ollama_client import OllamaClient
from src.utils.helpers import format_document_context, truncate_context
import config

logger = logging.getLogger(__name__)


class Generator:
    """
    Generates responses using LLM and retrieved context
    Focused on educational, helpful responses
    """
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or OllamaClient()
    
    def generate_educational_response(self, query: str, 
                                     context_chunks: List[Dict[str, Any]],
                                     stream: bool = False) -> str:
        """
        Generate educational response based on query and context
        
        Args:
            query: User question
            context_chunks: Retrieved relevant chunks
            stream: Whether to stream response
        
        Returns:
            Generated response
        """
        if not context_chunks:
            return self._generate_no_context_response(query)
        
        # Format context
        context_texts = [chunk['text'] for chunk in context_chunks]
        formatted_context = format_document_context(context_texts)
        
        # Truncate if too long
        formatted_context = truncate_context(formatted_context, max_tokens=4000)
        
        # Create educational prompt
        prompt = self._create_educational_prompt(query, formatted_context, context_chunks)
        
        # Generate response
        system_prompt = self._get_system_prompt()
        
        if stream:
            return self._generate_stream(prompt, system_prompt)
        else:
            response = self.ollama.generate(prompt, system=system_prompt)
            return response.strip()
    
    def generate_stream(self, query: str, 
                       context_chunks: List[Dict[str, Any]]) -> Iterator[str]:
        """
        Generate streaming response
        
        Yields:
            Response chunks as they are generated
        """
        if not context_chunks:
            prompt = f"Question: {query}\n\nPlease provide a helpful educational response."
        else:
            context_texts = [chunk['text'] for chunk in context_chunks]
            formatted_context = format_document_context(context_texts)
            formatted_context = truncate_context(formatted_context, max_tokens=4000)
            prompt = self._create_educational_prompt(query, formatted_context, context_chunks)
        
        system_prompt = self._get_system_prompt()
        
        for chunk in self.ollama.generate_stream(prompt, system=system_prompt):
            yield chunk
    
    def _create_educational_prompt(self, query: str, context: str,
                                  chunks: List[Dict[str, Any]]) -> str:
        """Create prompt optimized for educational responses"""
        
        # Check if context includes messy data analysis
        has_data_analysis = any('data_analysis' in chunk.get('metadata', {}).get('context', {}) 
                               for chunk in chunks)
        
        if has_data_analysis:
            prompt = f"""You are an educational AI assistant helping a user understand data they may not fully comprehend.

Context from documents:
{context}

User Question: {query}

Instructions:
1. Provide a clear, educational explanation based on the context
2. If the data is messy or unclear, explain what you can understand and what might be ambiguous
3. Use simple language and examples when explaining complex concepts
4. If interpreting data patterns, explain your reasoning
5. Encourage learning by explaining not just "what" but also "why" and "how"
6. If you're uncertain about something, say so clearly

Provide a helpful, educational response:"""
        else:
            prompt = f"""You are an educational AI assistant. Use the provided context to answer the user's question in an informative, educational manner.

Context from documents:
{context}

User Question: {query}

Instructions:
1. Answer based on the context provided
2. Explain concepts clearly and thoroughly
3. Use examples from the context when helpful
4. If the context doesn't fully answer the question, say what you can determine and what's missing
5. Focus on helping the user learn and understand
6. Be accurate and cite specific information from the context

Provide a clear, educational answer:"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for educational assistant"""
        return """You are an expert educational AI assistant. Your role is to:
- Help users learn and understand information from documents
- Provide clear, accurate, and well-reasoned explanations
- Use the provided context to give informed answers
- Explain complex concepts in accessible ways
- Be honest when information is uncertain or incomplete
- Focus on fostering understanding, not just providing answers"""
    
    def _generate_no_context_response(self, query: str) -> str:
        """Generate response when no relevant context is found"""
        prompt = f"""The user asked: "{query}"

However, no relevant information was found in the document database.

Provide a helpful response that:
1. Acknowledges that the information wasn't found in the available documents
2. Suggests the user might want to upload relevant documents
3. Offers general knowledge if appropriate (but clearly distinguish it from document-based answers)

Response:"""
        
        system_prompt = self._get_system_prompt()
        response = self.ollama.generate(prompt, system=system_prompt, temperature=0.5)
        
        return response.strip()
    
    def generate_summary(self, documents: List[str]) -> str:
        """Generate summary of multiple documents"""
        combined_text = "\n\n---\n\n".join(documents[:5])  # Limit to 5 docs
        combined_text = truncate_context(combined_text, max_tokens=6000)
        
        prompt = f"""Provide a comprehensive summary of these documents:

{combined_text}

Summary:"""
        
        summary = self.ollama.generate(prompt, temperature=0.3)
        return summary.strip()
    
    def explain_concept(self, concept: str, context: str) -> str:
        """Generate explanation of a specific concept from context"""
        prompt = f"""Explain the concept of "{concept}" based on this context:

{context}

Provide a clear, educational explanation:"""
        
        explanation = self.ollama.generate(prompt, temperature=0.4)
        return explanation.strip()


logger.info("Generator initialized")

