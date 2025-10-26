# 📚 ReasonableRAG - Intelligent Educational Document Assistant

An advanced offline RAG (Retrieval-Augmented Generation) system that can analyze ANY document type and provide intelligent, educational responses. Built to handle messy, unorganized, and complex data with AI-powered reasoning.

## ✨ Features

### 🔥 Core Capabilities
- **Multi-Format Support**: PDF, DOCX, TXT, CSV, XLSX, Images (with OCR)
- **Intelligent Data Understanding**: LLM-powered analysis of messy and unorganized data
- **Offline Operation**: Works completely offline using Ollama
- **Educational Focus**: Designed to help users learn and understand information
- **Vector Search**: FAISS-powered semantic search for accurate retrieval
- **Reasoning Engine**: Uses advanced LLMs to understand context and provide reasoned responses

### 🎯 Special Features
- **Messy Data Analyzer**: Specifically handles CSV/Excel files with no proper structure
- **Smart Chunking**: Semantic chunking with context preservation
- **Multi-Modal**: Supports text and image documents
- **Streaming Responses**: Real-time response generation
- **Document Summaries**: Automatic summarization of uploaded content
- **Key Concept Extraction**: Identifies important topics and themes

## 🚀 Quick Start

### Prerequisites
1. **Python 3.8+**
2. **Ollama** installed and running
3. Required Ollama models (see Installation)

### Installation

1. **Clone or navigate to project directory**
```bash
cd reasoning_rag
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR** (for image support)
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`

4. **Pull required Ollama models**
```bash
ollama pull qwen2.5:14b          # Main reasoning model
ollama pull nomic-embed-text     # Embedding model
ollama pull deepseek-r1:7b       # Fast reasoning model (optional)
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### 1. Upload Documents
- Navigate to the **"Upload Documents"** tab
- Upload one or multiple files (PDF, DOCX, CSV, XLSX, images, etc.)
- Click **"Process Documents"**
- Wait for AI to analyze and index your documents

### 2. Ask Questions
- Go to the **"Ask Questions"** tab
- Type your question in the chat input
- Get educational, well-reasoned responses based on your documents
- View sources and confidence scores

### 3. Analyze Messy Data
- Use the **"Analyze Messy Data"** tab for unorganized CSV/Excel files
- Upload your messy data file
- Get AI-powered analysis of what the data represents
- Receive guidance on how to interpret the information
- Optionally add to your knowledge base

### 4. Manage Documents
- View all uploaded documents in **"Document Library"**
- See summaries and statistics
- Delete documents if needed

## 🏗️ Architecture

```
reasoning_rag/
├── app.py                          # Streamlit UI
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── src/
│   ├── rag_pipeline.py            # Main orchestration pipeline
│   ├── ingestion/
│   │   ├── parsers.py             # Multi-format document parsers
│   │   └── preprocessor.py        # Intelligent LLM-based preprocessing
│   ├── vectorstore/
│   │   └── faiss_store.py         # FAISS vector database
│   ├── retrieval/
│   │   └── retriever.py           # Semantic search & retrieval
│   ├── generation/
│   │   └── generator.py           # Educational response generation
│   └── utils/
│       ├── helpers.py             # Utility functions
│       └── ollama_client.py       # Ollama API wrapper
├── vector_store/                   # Stored embeddings and metadata
├── uploaded_documents/             # Temporary upload storage
└── logs/                          # Application logs
```

## 🎛️ Configuration

Edit `config.py` to customize:

- **Models**: Change LLM and embedding models
- **Chunking**: Adjust chunk size and overlap
- **Retrieval**: Modify top-k and similarity thresholds
- **Paths**: Change storage locations

## 🧠 How It Works

### Document Processing Pipeline

1. **Parse**: Extract text, tables, and metadata from any format
2. **Reason**: LLM analyzes content and structure
3. **Chunk**: Create semantic chunks with rich context
4. **Embed**: Generate vector embeddings using Ollama
5. **Store**: Index in FAISS for fast retrieval

### Query Pipeline

1. **Understand**: Analyze user question
2. **Retrieve**: Semantic search for relevant chunks
3. **Rerank** (optional): LLM-based relevance scoring
4. **Generate**: Create educational response with citations
5. **Stream**: Real-time response delivery

### Messy Data Handling

When messy CSV/Excel data is detected:
1. LLM analyzes data structure and patterns
2. Generates interpretation of column meanings
3. Provides user-friendly explanation
4. Suggests ways to work with the data
5. Creates enriched chunks with analysis context

## 🔧 Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`
- Verify URL in config.py matches your Ollama instance

### Memory Issues
- Use smaller models (e.g., `qwen2.5:7b` instead of `14b`)
- Reduce chunk size in config.py
- Process fewer documents at once

### OCR Not Working
- Install Tesseract OCR
- Add Tesseract to system PATH
- Verify with: `tesseract --version`

### Slow Performance
- Use faster models for quick operations
- Disable reranking for faster responses
- Reduce top_k retrieval count

## 🎯 Use Cases

- **Study Assistant**: Upload textbooks and lecture notes, ask questions
- **Data Analysis Helper**: Understand messy CSV/Excel files
- **Research Tool**: Process research papers and extract insights
- **Document Q&A**: Query large document collections
- **Learning Aid**: Get explanations and educational content

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Cloud deployment option (Pinecone integration)
- [ ] Advanced visualization of document relationships
- [ ] Citation export and note-taking features
- [ ] Collaborative document sharing
- [ ] Fine-tuned reranking models

## 📝 Models Used

- **qwen2.5:14b**: Primary reasoning and generation (9GB)
- **nomic-embed-text**: Embeddings generation (274MB)
- **deepseek-r1:7b**: Fast operations and analysis (4.7GB)

Total storage: ~14GB

## 🤝 Contributing

This is a personal educational project, but suggestions and improvements are welcome!

## 📄 License

MIT License - Feel free to use and modify

## 🙏 Acknowledgments

- Ollama team for local LLM infrastructure
- FAISS for efficient vector search
- Streamlit for the amazing UI framework
- Open-source LLM community

## 💡 Tips for Best Results

1. **Upload Quality Documents**: Better input = better output
2. **Ask Specific Questions**: Clear questions get better answers
3. **Use Messy Data Analyzer**: For unclear datasets
4. **Check Sources**: Always verify important information
5. **Experiment with Settings**: Adjust retrieval parameters for your use case

---

**Built with ❤️ for learning and education**

For issues or questions, check the logs in `logs/reasoning_rag.log`

