# 🤖 Agentic RAG Demonstration

<div align="center">

![Agentic RAG](https://img.shields.io/badge/Agentic-RAG-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Demo-orange?style=for-the-badge)

</div>

## 📚 Overview

This project demonstrates an **Agentic RAG (Retrieval-Augmented Generation)** system designed for production environments. It showcases how to combine the capabilities of large language models with sophisticated retrieval mechanisms and agent-based planning to create a more powerful question-answering system.

Presented as part of a seminar on implementing Agentic RAG in production environments, this demonstration highlights best practices for building scalable, modular, and maintainable AI systems.

## ✨ Features

- **Agent-Based Planning**: Utilizes LLM-based planning to break down complex queries
- **Advanced Retrieval**: Smart document retrieval with context-aware filtering
- **Fact Checking**: Verification of generated information against retrieved data
- **Memory Management**: Short-term memory to maintain context in multi-turn conversations
- **Web Search Integration**: Capability to search the web for up-to-date information
- **Re-ranking System**: Optimizes relevance of retrieved information
- **Modular Architecture**: Clean separation of concerns for easier maintenance and scaling

## 🏗️ Architecture

The project is structured using clean architecture principles:

```
📦 src
 ┣ 📂 api             # API layer for external access
 ┣ 📂 application     # Application services that orchestrate domain services
 ┣ 📂 domain          # Core domain services implementing RAG capabilities
 │  ┣ 📂 answer_generator  # Generates final answers based on context
 │  ┣ 📂 get_fact          # Fact verification services
 │  ┣ 📂 memory            # Short-term memory management 
 │  ┣ 📂 planning          # Agent planning capabilities
 │  ┣ 📂 rerank            # Re-ranking retrieved documents
 │  ┣ 📂 retrive           # Document retrieval services
 │  ┗ 📂 web_searching     # Web search integration
 ┣ 📂 infra          # Infrastructure implementations
 │  ┣ 📂 llm              # LLM service abstractions
 │  ┗ 📂 milvus           # Vector database integration
 ┗ 📂 shared         # Shared utilities and configurations
    ┣ 📂 base             # Base classes and interfaces
    ┣ 📂 logging          # Logging configuration
    ┗ 📂 settings         # Application settings
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/tienndm/agentic-rag.git
cd agentic-rag
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## 🏄‍♂️ Usage

### Running the Demo

```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000`.

### Example Query

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the key components of an Agentic RAG system?"}'
```

## 🛠️ Development

The project follows a modular design pattern to separate concerns:

- **Domain Services**: Core RAG capabilities
- **Application Services**: Orchestration of domain services
- **API Layer**: External interfaces
- **Infrastructure**: External integrations (LLMs, databases)

## 📝 Seminar Notes

This demo accompanies a seminar on "Implementing Agentic RAG in Production" which covers:

- Challenges of traditional RAG systems
- Benefits of adding agency to RAG
- Architectural patterns for production deployment
- Performance optimization techniques
- Monitoring and evaluation strategies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

- Your Name - Tien Nguyen Do Minh

---

<div align="center">
  <p>Built with ❤️ for the AI community</p>
</div>