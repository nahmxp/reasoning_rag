"""
Intelligent data preprocessor with LLM reasoning
Handles messy, unstructured, and unorganized data
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import json
from src.utils.ollama_client import OllamaClient
from src.utils.helpers import chunk_text_semantic, clean_text
import config

logger = logging.getLogger(__name__)


class IntelligentPreprocessor:
    """
    Uses LLM to understand and reason about document content
    Especially useful for messy or unstructured data
    """
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or OllamaClient()
    
    def process_document(self, parsed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process parsed document with intelligent reasoning
        
        Args:
            parsed_doc: Output from DocumentParser
        
        Returns:
            Enhanced document with reasoning and structured chunks
        """
        if not parsed_doc.get('success', False):
            return parsed_doc
        
        file_type = parsed_doc.get('file_type', '')
        text = parsed_doc.get('text', '')
        metadata = parsed_doc.get('metadata', {})
        
        # Check if data is messy
        is_messy = metadata.get('is_messy', False)
        
        # Process based on file type and messiness
        if is_messy and file_type in ['.csv', '.xlsx', '.xls']:
            return self._process_messy_tabular(parsed_doc)
        else:
            return self._process_standard(parsed_doc)
    
    def _process_standard(self, parsed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process standard, well-structured documents"""
        text = parsed_doc.get('text', '')
        
        if not text or len(text) < 50:
            logger.warning("Document has minimal content")
            return parsed_doc
        
        # Generate document summary
        summary = self._generate_summary(text)
        
        # Create semantic chunks with context
        chunks = self._create_enriched_chunks(text, summary, parsed_doc['metadata'])
        
        # Identify key concepts
        key_concepts = self._extract_key_concepts(text)
        
        # Update document
        parsed_doc['summary'] = summary
        parsed_doc['chunks'] = chunks
        parsed_doc['key_concepts'] = key_concepts
        parsed_doc['processed'] = True
        
        return parsed_doc
    
    def _process_messy_tabular(self, parsed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process messy CSV/Excel data with LLM assistance.
        Creates structured, searchable representation of the analyzed data.
        """
        logger.info("Processing messy tabular data with LLM reasoning")
        
        text = parsed_doc.get('text', '')
        tables = parsed_doc.get('tables', [])
        metadata = parsed_doc.get('metadata', {})
        
        if not tables:
            return self._process_standard(parsed_doc)
        
        # Get more context for analysis (up to 10k chars for better understanding)
        analysis_text = text[:10000] if len(text) > 10000 else text
        
        # Analyze the structure with LLM
        analysis = self._analyze_messy_data(analysis_text)
        
        # Generate helpful interpretation
        interpretation = self._interpret_data_structure(analysis_text, analysis)
        
        # Try to create a structured representation (if possible)
        structured_summary = self._create_structured_summary(text[:5000], analysis)
        
        # Create enriched chunks WITH analysis embedded in text
        chunks = self._create_tabular_chunks(text, analysis, interpretation, structured_summary)
        
        # Update document
        parsed_doc['data_analysis'] = analysis
        parsed_doc['interpretation'] = interpretation
        parsed_doc['structured_summary'] = structured_summary
        parsed_doc['chunks'] = chunks
        parsed_doc['processed'] = True
        
        logger.info(f"Processed messy tabular data: {len(chunks)} chunks created with embedded analysis")
        
        return parsed_doc
    
    def _generate_summary(self, text: str, max_length: int = 2000) -> str:
        """Generate concise summary of document"""
        # Truncate if too long
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        prompt = f"""Analyze the following document and provide a concise summary that captures:
1. Main topic/subject
2. Key points and important information
3. Type of content (educational, technical, data, narrative, etc.)

Document:
{text}

Provide a clear, informative summary in 3-5 sentences:"""
        
        try:
            system_prompt = "You are an expert document analyst. Provide clear, accurate summaries."
            summary = self.ollama.generate(prompt, system=system_prompt, 
                                          model=config.FAST_LLM_MODEL)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Summary generation failed."
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts and topics from text"""
        if len(text) > 8000:
            text = text[:8000]
        
        prompt = f"""Extract the main concepts, topics, and keywords from this text.
List them as a comma-separated list of single words or short phrases (2-3 words max).
Focus on the most important and relevant concepts.

Text:
{text}

Key concepts (comma-separated):"""
        
        try:
            concepts_text = self.ollama.generate(prompt, model=config.FAST_LLM_MODEL,
                                                temperature=0.3)
            # Parse comma-separated concepts
            concepts = [c.strip() for c in concepts_text.split(',') if c.strip()]
            return concepts[:20]  # Top 20 concepts
        except Exception as e:
            logger.error(f"Error extracting concepts: {e}")
            return []
    
    def _analyze_messy_data(self, data_preview: str) -> str:
        """Analyze messy tabular data structure"""
        prompt = f"""Analyze this messy/unorganized tabular data and describe:
1. What kind of data this appears to be
2. What each column might represent (make educated guesses)
3. Any patterns or structure you can identify
4. Potential issues with the data organization

Data:
{data_preview}

Analysis:"""
        
        try:
            analysis = self.ollama.generate(prompt, temperature=0.2)
            return analysis.strip()
        except Exception as e:
            logger.error(f"Error analyzing messy data: {e}")
            return "Analysis failed."
    
    def _interpret_data_structure(self, data_preview: str, analysis: str) -> str:
        """Generate helpful interpretation for user"""
        prompt = f"""Based on this data analysis, provide helpful guidance to a user who doesn't understand this data:

Data Preview:
{data_preview}

Analysis:
{analysis}

Provide user-friendly explanation:
1. What this data represents in simple terms
2. How to interpret the information
3. What questions they could ask about this data

Explanation:"""
        
        try:
            interpretation = self.ollama.generate(prompt, temperature=0.3)
            return interpretation.strip()
        except Exception as e:
            logger.error(f"Error generating interpretation: {e}")
            return "Interpretation failed."
    
    def _create_enriched_chunks(self, text: str, summary: str, 
                               metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create semantic chunks with rich context"""
        # Use semantic chunking
        base_chunks = chunk_text_semantic(text)
        
        # Enrich each chunk with context
        enriched_chunks = []
        for chunk_data in base_chunks:
            chunk_text = chunk_data['text']
            
            enriched_chunk = {
                'text': chunk_text,
                'chunk_index': chunk_data['chunk_index'],
                'context': {
                    'document_summary': summary,
                    'file_name': metadata.get('file_name', ''),
                    'chunk_position': f"{chunk_data['chunk_index'] + 1} of {len(base_chunks)}"
                },
                'metadata': chunk_data
            }
            enriched_chunks.append(enriched_chunk)
        
        return enriched_chunks
    
    def _create_structured_summary(self, text: str, analysis: str) -> str:
        """
        Create a structured summary of the data that can be easily searched
        """
        prompt = f"""Based on this data analysis, create a structured summary that includes:
1. What each column likely represents (if identifiable)
2. Data types and patterns observed
3. Key insights about the data structure
4. Suggested questions users might ask about this data

Data Preview:
{text[:3000]}

Analysis:
{analysis}

Structured Summary:"""
        
        try:
            summary = self.ollama.generate(prompt, model=config.FAST_LLM_MODEL, temperature=0.2)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error creating structured summary: {e}")
            return ""
    
    def _create_tabular_chunks(self, text: str, analysis: str, 
                              interpretation: str, structured_summary: str = "") -> List[Dict[str, Any]]:
        """
        Create chunks for tabular data with LLM insights.
        IMPORTANT: Includes analysis/interpretation in the text field so it's embedded
        and searchable in vector store.
        """
        # Split text into manageable chunks
        base_chunks = chunk_text_semantic(text, chunk_size=1200)  # Reduced to fit analysis
        
        # Create a comprehensive metadata chunk with analysis/interpretation (always searchable)
        metadata_text = f"""DATA STRUCTURE ANALYSIS AND INTERPRETATION:

=== DATA ANALYSIS ===
{analysis}

=== INTERPRETATION & GUIDANCE ===
{interpretation}"""
        
        if structured_summary:
            metadata_text += f"""

=== STRUCTURED SUMMARY ===
{structured_summary}"""
        
        metadata_text += """

This data has been analyzed and interpreted. The analysis above describes the structure, meaning, and patterns in the data."""
        
        metadata_chunk = {
            'text': metadata_text,
            'chunk_index': -1,  # Special index for metadata chunk
            'context': {
                'data_type': 'tabular',
                'chunk_type': 'analysis_metadata',
                'analysis': analysis,
                'interpretation': interpretation,
                'structured_summary': structured_summary
            },
            'metadata': {'is_analysis_chunk': True}
        }
        
        enriched_chunks = [metadata_chunk]  # Add analysis chunk first
        
        # Enrich each data chunk with analysis context
        for idx, chunk_data in enumerate(base_chunks):
            # Prepend analysis context to make it searchable
            enriched_text = f"""DATA CONTEXT (from AI analysis):
{analysis}

ACTUAL DATA:
{chunk_data['text']}

NOTE: {interpretation[:200]}"""
            
            enriched_chunk = {
                'text': enriched_text,  # Include analysis in embedded text!
                'chunk_index': idx,
                'context': {
                    'data_type': 'tabular',
                    'analysis': analysis,
                    'interpretation': interpretation,
                    'chunk_position': f"{idx + 1} of {len(base_chunks)}",
                    'has_analysis_context': True
                },
                'metadata': chunk_data
            }
            enriched_chunks.append(enriched_chunk)
        
        logger.info(f"Created {len(enriched_chunks)} chunks for tabular data (including 1 analysis chunk)")
        return enriched_chunks
    
    def reason_about_content(self, text: str, question: str) -> str:
        """
        Use LLM to reason about specific content
        
        Args:
            text: Document text
            question: Specific question about the content
        
        Returns:
            Reasoned response
        """
        prompt = f"""Based on the following content, answer this question with detailed reasoning:

Content:
{text[:5000]}

Question: {question}

Provide a thoughtful, well-reasoned answer:"""
        
        try:
            response = self.ollama.generate(prompt, temperature=0.3)
            return response.strip()
        except Exception as e:
            logger.error(f"Error reasoning about content: {e}")
            return "Unable to reason about this content."


logger.info("Intelligent preprocessor initialized")

