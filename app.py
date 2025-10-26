"""
Streamlit UI for ReasonableRAG System
"""
import streamlit as st
import os
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_pipeline import RAGPipeline
import config

# Page configuration
st.set_page_config(
    page_title="ReasonableRAG - Educational Document Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .messy-data-alert {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = RAGPipeline()
    st.session_state.chat_history = []
    st.session_state.uploaded_files = []


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">📚 ReasonableRAG</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your Intelligent Educational Document Assistant</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Check Ollama status
        if st.session_state.rag_pipeline.check_ollama():
            st.success("✅ Ollama Connected")
        else:
            st.error("❌ Ollama Not Available")
            st.info("Please ensure Ollama is running on http://localhost:11434")
        
        st.divider()
        
        # System stats
        st.subheader("📊 System Stats")
        stats = st.session_state.rag_pipeline.get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", stats['total_documents'])
            st.metric("Chunks", stats['total_chunks'])
        with col2:
            st.metric("Models", len(stats['models_available']))
        
        st.divider()

        # Model selection
        st.subheader("🧠 Model Selection")
        models = stats.get('models_available', []) or []
        default_model = config.LLM_MODEL
        model_options = models if len(models) > 0 else [default_model]

        # Persist selected model in session state
        if 'selected_model' not in st.session_state:
            # prefer default if present in options
            try:
                default_index = model_options.index(default_model) if default_model in model_options else 0
            except Exception:
                default_index = 0
            st.session_state.selected_model = model_options[default_index]

        selected_model = st.selectbox(
            "Choose LLM model to use",
            options=model_options,
            index=model_options.index(st.session_state.selected_model) if st.session_state.get('selected_model') in model_options else 0,
            help="Select which Ollama model to use for generation"
        )

        # Apply selected model to the pipeline's Ollama client
        if selected_model:
            st.session_state.selected_model = selected_model
            try:
                st.session_state.rag_pipeline.ollama.llm_model = selected_model
            except Exception:
                # If assignment fails, continue without crashing the UI
                pass
        
        # Settings
        st.subheader("🎛️ Query Settings")
        top_k = st.slider("Number of chunks to retrieve", 1, 10, config.TOP_K_RETRIEVAL)
        use_rerank = st.checkbox("Use LLM Reranking", value=False, 
                                help="More accurate but slower")
        
        st.divider()
        
        # Clear data
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.session_state.rag_pipeline.vector_store.get_stats()['total_chunks'] > 0:
                st.session_state.rag_pipeline.vector_store.clear()
                st.session_state.rag_pipeline.vector_store.save()
                st.session_state.chat_history = []
                st.success("All data cleared!")
                st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Documents", "💬 Ask Questions", 
                                       "🔍 Analyze Messy Data", "📋 Document Library"])
    
    # Tab 1: Upload Documents
    with tab1:
        st.header("Upload Documents")
        st.write("Upload any document to build your knowledge base. Supports PDF, DOCX, TXT, CSV, XLSX, and images.")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'docx', 'doc', 'txt', 'csv', 'xlsx', 'xls', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload multiple documents at once"
        )
        
        if uploaded_files:
            if st.button("📥 Process Documents", type="primary"):
                process_documents(uploaded_files)
    
    # Tab 2: Ask Questions
    with tab2:
        st.header("Ask Questions")
        
        if stats['total_chunks'] == 0:
            st.info("👆 Please upload documents first to start asking questions!")
        else:
            # Chat interface
            st.write(f"Ask questions about your {stats['total_documents']} uploaded document(s)")
            
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
                    if "sources" in message and message["sources"]:
                        with st.expander("📚 View Sources"):
                            for i, source in enumerate(message["sources"], 1):
                                st.markdown(f"**Source {i}** (Score: {source['score']:.2f}) - {source['file_name']}")
                                st.text(source['text'])
            
            # User input
            user_question = st.chat_input("Ask a question about your documents...")
            
            if user_question:
                # Add user message to chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_question
                })
                
                # Display user message
                with st.chat_message("user"):
                    st.write(user_question)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        result = st.session_state.rag_pipeline.query(
                            user_question,
                            top_k=top_k,
                            use_rerank=use_rerank
                        )
                        
                        st.write(result['answer'])
                        
                        # Show sources
                        if result['sources']:
                            with st.expander("📚 View Sources"):
                                for i, source in enumerate(result['sources'], 1):
                                    st.markdown(f"**Source {i}** (Score: {source['score']:.2f}) - {source['file_name']}")
                                    st.text(source['text'])
                        
                        # Add assistant message to chat
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": result['answer'],
                            "sources": result['sources']
                        })
    
    # Tab 3: Analyze Messy Data
    with tab3:
        st.header("Analyze Messy/Unorganized Data")
        st.write("Upload messy CSV/Excel files or unstructured data for AI-powered analysis")
        
        messy_file = st.file_uploader(
            "Upload messy data file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload a CSV or Excel file you don't understand",
            key="messy_upload"
        )
        
        if messy_file:
            if st.button("🔍 Analyze Data", type="primary"):
                analyze_messy_data(messy_file)
    
    # Tab 4: Document Library
    with tab4:
        st.header("Document Library")
        
        if stats['total_documents'] == 0:
            st.info("No documents uploaded yet.")
        else:
            st.write(f"Managing {stats['total_documents']} document(s)")
            
            # Show processed documents
            for doc_hash, doc_info in st.session_state.rag_pipeline.processed_docs.items():
                with st.expander(f"📄 {doc_info['file_name']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Type:** {doc_info['file_type']}")
                        st.write(f"**Chunks:** {doc_info['chunks']}")
                    
                    with col2:
                        if doc_info.get('is_messy', False):
                            st.warning("⚠️ Messy Data Detected")
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"del_{doc_hash}"):
                            result = st.session_state.rag_pipeline.delete_document(doc_info['file_name'])
                            st.success(f"Deleted {result['chunks_removed']} chunks")
                            st.rerun()
                    
                    if doc_info.get('summary'):
                        st.write("**Summary:**")
                        st.info(doc_info['summary'])


def process_documents(uploaded_files):
    """Process uploaded documents"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        # Save uploaded file temporarily
        temp_path = os.path.join(config.UPLOAD_DIR, uploaded_file.name)
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Process document
        status_text.text(f"Processing {uploaded_file.name}...")
        result = st.session_state.rag_pipeline.ingest_document(temp_path)
        results.append(result)
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    # Show results
    status_text.empty()
    progress_bar.empty()
    
    for result in results:
        if result['status'] == 'success':
            st.success(f"✅ {os.path.basename(result['file_path'])}: Added {result['chunks_added']} chunks")
            
            if result.get('is_messy', False):
                st.warning(f"⚠️ Messy data detected in {os.path.basename(result['file_path'])}")
                
                if result.get('data_analysis'):
                    with st.expander("📊 View Data Analysis"):
                        st.write(result['data_analysis'])
            
            if result.get('summary'):
                with st.expander("📝 View Summary"):
                    st.info(result['summary'])
        
        elif result['status'] == 'already_processed':
            st.info(f"ℹ️ {os.path.basename(result['file_path'])}: Already in database")
        
        else:
            st.error(f"❌ {os.path.basename(result['file_path'])}: {result.get('error', 'Unknown error')}")
    
    # Refresh stats
    st.rerun()


def analyze_messy_data(uploaded_file):
    """Analyze messy data file"""
    # Save uploaded file temporarily
    temp_path = os.path.join(config.UPLOAD_DIR, uploaded_file.name)
    with open(temp_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner("Analyzing data with AI..."):
        result = st.session_state.rag_pipeline.analyze_messy_data(temp_path)
    
    if result['status'] == 'success':
        st.success(f"✅ Analysis complete for {result['file_name']}")
        
        if result.get('is_messy', False):
            st.markdown('<div class="messy-data-alert">⚠️ <strong>Messy Data Detected</strong></div>', 
                       unsafe_allow_html=True)
        
        # Show analysis
        if result.get('analysis'):
            st.subheader("📊 Data Structure Analysis")
            st.write(result['analysis'])
        
        # Show interpretation
        if result.get('interpretation'):
            st.subheader("💡 Interpretation & Guidance")
            st.info(result['interpretation'])
        
        # Show summary
        if result.get('summary'):
            st.subheader("📝 Summary")
            st.write(result['summary'])
        
        # Show suggestions
        if result.get('suggestions'):
            st.subheader("🎯 Suggestions")
            for suggestion in result['suggestions']:
                st.write(f"• {suggestion}")
        
        # Option to add to database
        if st.button("➕ Add to Document Database", type="primary"):
            ingest_result = st.session_state.rag_pipeline.ingest_document(temp_path)
            if ingest_result['status'] == 'success':
                st.success(f"Added to database: {ingest_result['chunks_added']} chunks")
                st.rerun()
    else:
        st.error(f"Error analyzing file: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()

