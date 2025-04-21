# 🤖 Agentic RAG Demonstration

<div align="center">

![Agentic RAG](https://img.shields.io/badge/Agentic-RAG-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Demo-orange?style=for-the-badge)

</div>

## 📚 Overview

This project demonstrates an **Agentic RAG (Retrieval-Augmented Generation)** system designed for production environments. It showcases how to combine the capabilities of large language models with specialized agents for different types of tasks. The system features a central query router that directs requests to the appropriate specialized agent based on the query type.

Presented as part of a seminar on implementing Agentic RAG in production environments, this demonstration highlights best practices for building scalable, modular, and maintainable AI systems.

## ✨ Features

- **Multi-Agent System**: Routes queries to specialized agents based on query type
- **Query Router**: Central dispatcher that determines which agent should handle a request
- **RAG Agent**: Sophisticated retrieval and generation agent for knowledge-based queries
- **Math Solving Agent**: Specialized agent for handling mathematical problems
- **Agent-Based Planning**: Utilizes LLM-based planning to break down complex queries
- **Memory Management**: Short-term memory to maintain context in multi-turn conversations
- **Web Search Integration**: Capability to search the web for up-to-date information
- **Modular Architecture**: Clean separation of concerns for easier maintenance and scaling

## 🏗️ Architecture

The project is structured using clean architecture principles with specialized components:

```
📦 src
 ┣ 📂 query         # Router component that dispatches requests to appropriate agents
 │  ┣ 📂 api          # API layer for external access and routing
 │  ┣ 📂 application  # Application services that orchestrate routing logic
 │  ┣ 📂 domain       # Core domain services for query processing
 │  ┣ 📂 infra        # Infrastructure implementations (LLM, Milvus)
 │  ┗ 📂 shared       # Shared utilities and configurations
 │
 ┣ 📂 retriver      # RAG agent for knowledge-based queries
 │  ┣ 📂 domain       # Core RAG capabilities
 │  │  ┣ 📂 answer_generator  # Generates final answers based on context
 │  │  ┣ 📂 get_fact          # Fact verification services
 │  │  ┣ 📂 memory            # Short-term memory management
 │  │  ┣ 📂 planning          # Agent planning capabilities
 │  │  ┣ 📂 rerank            # Re-ranking retrieved documents
 │  │  ┣ 📂 retrive           # Document retrieval services
 │  │  ┗ 📂 web_searching     # Web search integration
 │  ┣ 📂 infra        # Infrastructure implementations
 │  ┗ 📂 shared       # Shared utilities and configurations
 │
 ┗ 📂 solving       # Mathematical problem-solving agent
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)

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
pip install -r src/query/requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## 🏄‍♂️ Usage

### Running with Docker

```bash
cd scripts
docker-compose up -d
```

The API will be available at `http://localhost:8000`.

### Running Locally

```bash
cd src/query
python main.py
```

### Example Query

```bash
# General knowledge query (routed to RAG agent)
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the key components of an Agentic RAG system?"}'

# Math problem (routed to solving agent)
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Solve for x: 2x + 5 = 15"}'
```

## 🛠️ System Components

### Query Router
The query component acts as a central dispatcher that analyzes incoming queries and routes them to the appropriate specialized agent. It determines whether a query should be handled by the RAG agent for knowledge retrieval or the math solving agent for mathematical problems.

### RAG Agent (Retriever)
The retriever component implements a full Retrieval-Augmented Generation system with:
- Document retrieval with vector search
- Planning for complex queries
- Fact checking against reliable sources
- Re-ranking to prioritize most relevant information
- Web search integration for up-to-date information

### Math Solving Agent
A specialized agent for handling mathematical problems, equations, and calculations with:
- Step-by-step problem solving
- Equation parsing
- Formula application
- Calculation verification

## 📝 Seminar Notes

This demo accompanies a seminar on "Implementing Agentic RAG in Production" which covers:

- Benefits of specialized agents in AI systems
- Router design for query classification
- Architectural patterns for production deployment
- Performance optimization techniques
- Monitoring and evaluation strategies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

- Tien Nguyen Do Minh

---

<div align="center">
  <p>Built with ❤️ for the AI community</p>
</div>
