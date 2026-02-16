"""
Main RAG pipeline orchestrating all components
"""
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.ingestion.parsers import DocumentParser
from src.ingestion.preprocessor import IntelligentPreprocessor
from src.vectorstore.faiss_store import FAISSVectorStore
from src.retrieval.retriever import Retriever
from src.generation.generator import Generator
from src.utils.ollama_client import OllamaClient
from src.utils.helpers import get_file_hash, save_metadata, load_metadata
import config

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline for document processing and question answering
    """
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.parser = DocumentParser()
        self.preprocessor = IntelligentPreprocessor(self.ollama)
        self.vector_store = FAISSVectorStore(self.ollama)
        self.retriever = Retriever(self.vector_store, self.ollama)
        self.generator = Generator(self.ollama)
        
        # Track processed documents
        self.processed_docs = load_metadata()
    
    def check_ollama(self) -> bool:
        """Check if Ollama is available"""
        return self.ollama.is_available()
    
    def ingest_document(self, file_path: str, save_to_store: bool = True) -> Dict[str, Any]:
        """
        Ingest a document into the RAG system
        
        Args:
            file_path: Path to document
            save_to_store: Whether to save to vector store
        
        Returns:
            Processing result with status and metadata
        """
        logger.info(f"Ingesting document: {file_path}")
        
        # Check if already processed
        file_hash = get_file_hash(file_path)
        if file_hash in self.processed_docs:
            logger.info(f"Document already processed: {file_path}")
            return {
                'status': 'already_processed',
                'file_path': file_path,
                'message': 'Document already in database'
            }
        
        try:
            # Step 1: Parse document
            parsed_doc = self.parser.parse(file_path)
            
            if not parsed_doc['success']:
                return {
                    'status': 'error',
                    'file_path': file_path,
                    'error': parsed_doc.get('error', 'Unknown error')
                }
            
            # Step 2: Intelligent preprocessing with LLM reasoning
            processed_doc = self.preprocessor.process_document(parsed_doc)
            
            # Step 3: Add to vector store
            if save_to_store and 'chunks' in processed_doc:
                chunks_added = self.vector_store.add_documents(processed_doc['chunks'])
                
                # Save vector store
                self.vector_store.save()
                
                # Track processed document
                self.processed_docs[file_hash] = {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'chunks': chunks_added,
                    'summary': processed_doc.get('summary', ''),
                    'file_type': processed_doc.get('file_type', ''),
                    'is_messy': processed_doc.get('metadata', {}).get('is_messy', False)
                }
                save_metadata(self.processed_docs)
                
                logger.info(f"Successfully ingested {file_path}: {chunks_added} chunks")
                
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'chunks_added': chunks_added,
                    'summary': processed_doc.get('summary', ''),
                    'is_messy': processed_doc.get('metadata', {}).get('is_messy', False),
                    'data_analysis': processed_doc.get('data_analysis', ''),
                    'interpretation': processed_doc.get('interpretation', '')
                }
            else:
                return {
                    'status': 'processed_no_store',
                    'file_path': file_path,
                    'processed_doc': processed_doc
                }
        
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {e}")
            return {
                'status': 'error',
                'file_path': file_path,
                'error': str(e)
            }
    
    def query(self, question: str, top_k: int = config.TOP_K_RETRIEVAL,
              use_rerank: bool = False) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            use_rerank: Whether to use LLM reranking
        
        Returns:
            Answer and relevant context
        """
        logger.info(f"Processing query: {question}")
        
        try:
            # Retrieve relevant context
            if use_rerank:
                context_chunks = self.retriever.retrieve_with_rerank(question, top_k=top_k * 2)
            else:
                context_chunks = self.retriever.retrieve(question, top_k=top_k)
            
            # Generate response
            answer = self.generator.generate_educational_response(question, context_chunks)
            
            # Format sources
            sources = []
            for chunk in context_chunks:
                metadata = chunk.get('metadata', {})
                context = metadata.get('context', {})
                sources.append({
                    'text': chunk['text'][:200] + '...',
                    'score': chunk['score'],
                    'file_name': context.get('file_name', 'Unknown'),
                    'chunk_position': context.get('chunk_position', '')
                })
            
            return {
                'answer': answer,
                'sources': sources,
                'num_chunks_used': len(context_chunks),
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'answer': f"Error processing query: {str(e)}",
                'sources': [],
                'num_chunks_used': 0,
                'success': False,
                'error': str(e)
            }
    
    def query_stream(self, question: str, top_k: int = config.TOP_K_RETRIEVAL):
        """
        Query with streaming response
        
        Yields:
            Response chunks as they are generated
        """
        # Retrieve context
        context_chunks = self.retriever.retrieve(question, top_k=top_k)
        
        # Stream response
        for chunk in self.generator.generate_stream(question, context_chunks):
            yield chunk
    
    def analyze_messy_data(self, file_path: str) -> Dict[str, Any]:
        """
        Special analysis for messy/unorganized data
        
        Args:
            file_path: Path to messy data file
        
        Returns:
            Analysis and interpretation
        """
        logger.info(f"Analyzing messy data: {file_path}")
        
        # Parse document
        parsed_doc = self.parser.parse(file_path)
        
        if not parsed_doc['success']:
            return {
                'status': 'error',
                'error': parsed_doc.get('error', 'Unknown error')
            }
        
        # Process with special attention to messy data
        processed_doc = self.preprocessor.process_document(parsed_doc)
        
        return {
            'status': 'success',
            'file_name': os.path.basename(file_path),
            'is_messy': processed_doc.get('metadata', {}).get('is_messy', False),
            'analysis': processed_doc.get('data_analysis', 'No special analysis needed'),
            'interpretation': processed_doc.get('interpretation', ''),
            'summary': processed_doc.get('summary', ''),
            'suggestions': self._generate_data_suggestions(processed_doc)
        }
    
    def _generate_data_suggestions(self, processed_doc: Dict[str, Any]) -> List[str]:
        """Generate helpful suggestions for working with the data"""
        suggestions = []
        
        if processed_doc.get('metadata', {}).get('is_messy', False):
            suggestions.append("This data appears unorganized. Consider restructuring it for better analysis.")
            suggestions.append("Try asking specific questions about what you'd like to understand from this data.")
        
        if 'key_concepts' in processed_doc:
            concepts = processed_doc['key_concepts'][:5]
            suggestions.append(f"Key topics found: {', '.join(concepts)}")
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        vector_stats = self.vector_store.get_stats()
        
        return {
            'total_documents': len(self.processed_docs),
            'total_chunks': vector_stats['total_chunks'],
            'unique_documents': vector_stats['unique_documents'],
            'models_available': self.ollama.list_models(),
            'ollama_available': self.ollama.is_available()
        }
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a document from the system
        
        Args:
            filename: Name of file to delete
        
        Returns:
            Deletion result
        """
        # Find and remove from processed docs
        hash_to_remove = None
        for file_hash, doc_info in self.processed_docs.items():
            if doc_info['file_name'] == filename:
                hash_to_remove = file_hash
                break
        
        if hash_to_remove:
            del self.processed_docs[hash_to_remove]
            save_metadata(self.processed_docs)
        
        # Remove from vector store
        chunks_removed = self.vector_store.delete_by_filename(filename)
        
        if chunks_removed > 0:
            self.vector_store.save()
        
        return {
            'status': 'success',
            'chunks_removed': chunks_removed,
            'filename': filename
        }


logger.info("RAG Pipeline initialized")

