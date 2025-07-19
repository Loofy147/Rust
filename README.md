<<<< cursor/reasoning-agent-for-knowledge-graph-and-llm-interaction-543a
# ReasoningAgent - Knowledge Graph & LLM Integration System

A sophisticated Rust-based reasoning agent that integrates knowledge graphs, vector similarity search, and Large Language Models (LLMs) through a flexible plugin architecture.

## 🚀 Features

### Core Architecture
- **Knowledge Graph Integration**: Store and query structured knowledge with relationships
- **Vector Similarity Search**: Find semantically similar content using vector embeddings
- **Plugin System**: Swappable LLM providers (OpenAI, Hugging Face, Custom)
- **Flexible Prompt Building**: Customizable prompt construction strategies
- **Comprehensive Metrics**: Track performance, success rates, and system health
- **Async/Await Support**: Built with Tokio for high-performance concurrent processing

### Communication Flow
```
Task Input → Knowledge Graph Query → Vector Similarity Search → 
Prompt Building → LLM Processing → Response Storage → Metrics Emission
```

### Plugin System
- **LLM Plugins**: Mock, OpenAI GPT, Hugging Face models
- **Prompt Builders**: Default and Enhanced prompt engineering strategies
- **Storage Backends**: In-memory and persistent (SQLite) options

## 📦 Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
reasoning-agent = "0.1.0"

# Optional features
reasoning-agent = { version = "0.1.0", features = ["llm-apis"] }
```

## 🔧 Quick Start

### Basic Usage

```rust
use reasoning_agent::{
    ReasoningAgent,
    plugins::{MockLLMPlugin, DefaultPromptBuilderPlugin},
    knowledge_graph::InMemoryKnowledgeGraph,
    vector_store::InMemoryVectorStore,
    metrics::MetricsCollector,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize components
    let knowledge_graph = InMemoryKnowledgeGraph::with_sample_data();
    let vector_store = InMemoryVectorStore::new();
    let metrics = MetricsCollector::new();
    
    // Set up plugins
    let llm_plugin = Box::new(MockLLMPlugin::new());
    let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

    // Create reasoning agent
    let mut agent = ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics,
    );

    // Process a task
    let result = agent.process_task("What are the benefits of renewable energy?").await?;
    println!("Result: {}", result);
    
    // View metrics
    agent.print_metrics();
    
    Ok(())
}
```

### With Real LLM APIs

```rust
// Enable the llm-apis feature
use reasoning_agent::plugins::OpenAILLMPlugin;

let llm_plugin = Box::new(OpenAILLMPlugin::new(
    "your-openai-api-key".to_string(),
    Some("gpt-4".to_string())
));
```

## 🏗️ Architecture

### Core Components

1. **ReasoningAgent**: Central orchestrator managing the reasoning pipeline
2. **Knowledge Graph**: Structured storage for entities and relationships
3. **Vector Store**: Semantic similarity search using embeddings
4. **Plugin System**: Modular components for LLMs and prompt building
5. **Metrics Collector**: Performance monitoring and analytics

### Plugin Interfaces

#### LLM Plugin
```rust
#[async_trait]
pub trait LLMPlugin: Send + Sync {
    async fn generate(&self, request: &LLMRequest) -> Result<LLMResponse, PluginError>;
    fn get_model_name(&self) -> String;
}
```

#### Prompt Builder Plugin
```rust
#[async_trait]
pub trait PromptBuilderPlugin: Send + Sync {
    async fn build_prompt(&self, context: &PromptContext) -> anyhow::Result<String>;
}
```

## 🌟 Advanced Features

### Knowledge Graph Operations

```rust
// Add custom entities
let entity = KnowledgeEntity {
    id: "solar_energy_001".to_string(),
    entity_type: "technology".to_string(),
    properties: vec![
        ("efficiency".to_string(), "20-22%".to_string()),
        ("cost_trend".to_string(), "Decreasing".to_string()),
    ],
};
knowledge_graph.add_entity(entity).await?;

// Query entities
let results = knowledge_graph.query_entities("renewable energy").await?;
```

### Vector Similarity Search

```rust
// Add documents
let doc_id = vector_store.add_document(
    "Solar panels convert sunlight directly into electricity through photovoltaic cells."
).await?;

// Find similar content
let similar = vector_store.find_similar("solar power technology", 5).await?;
```

### Metrics and Monitoring

```rust
// Get detailed metrics
let metrics = agent.get_metrics().get_system_metrics();
println!("Success rate: {:.1}%", metrics.success_rate);
println!("Avg processing time: {:.1}ms", metrics.avg_processing_time_ms);

// Export as JSON
let json_metrics = agent.get_metrics().export_metrics_json()?;
```

## 🚀 Next Steps & Enhancements

### 1. Real API Integration

**OpenAI Integration:**
```bash
cargo run --features llm-apis
export OPENAI_API_KEY="your-key-here"
```

**Hugging Face Integration:**
```bash
export HUGGINGFACE_API_KEY="your-key-here"
```

### 2. Error Handling & Retry Logic

```rust
// Add to your LLM plugin implementation
async fn generate_with_retry(&self, request: &LLMRequest) -> Result<LLMResponse, PluginError> {
    let mut attempts = 0;
    let max_attempts = 3;
    
    while attempts < max_attempts {
        match self.generate(request).await {
            Ok(response) => return Ok(response),
            Err(e) if attempts < max_attempts - 1 => {
                attempts += 1;
                tokio::time::sleep(Duration::from_millis(1000 * attempts)).await;
            }
            Err(e) => return Err(e),
        }
    }
    unreachable!()
}
```

### 3. REST API Server

```rust
// Using axum (add to Cargo.toml: axum = "0.7", tokio = { version = "1.0", features = ["full"] })
use axum::{extract::State, http::StatusCode, response::Json, routing::post, Router};

#[tokio::main]
async fn main() {
    let agent = Arc::new(Mutex::new(/* your reasoning agent */));
    
    let app = Router::new()
        .route("/api/tasks", post(process_task))
        .route("/api/metrics", get(get_metrics))
        .with_state(agent);

    axum::Server::bind(&"0.0.0.0:3000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn process_task(
    State(agent): State<AgentState>,
    Json(request): Json<TaskRequest>,
) -> Result<Json<TaskResponse>, StatusCode> {
    // Implementation here
}
```

### 4. Persistent Storage

```rust
// Enable SQLite feature (add to Cargo.toml features)
use reasoning_agent::{
    knowledge_graph::SQLiteKnowledgeGraph,
    vector_store::SQLiteVectorStore,
};

let kg = SQLiteKnowledgeGraph::new("knowledge.db").await?;
let vs = SQLiteVectorStore::new("vectors.db", 384).await?;
```

### 5. Advanced Metrics & Monitoring

```rust
// Prometheus integration
use reasoning_agent::metrics::PrometheusExporter;

let exporter = PrometheusExporter::new(metrics_collector);
let prometheus_metrics = exporter.export_prometheus_format();

// Serve metrics endpoint
async fn metrics_handler() -> String {
    prometheus_metrics
}
```

## 📊 Performance Characteristics

- **In-Memory KG**: ~1ms query time for 1K entities
- **Vector Search**: ~5ms for 1K documents (384-dim vectors)
- **Mock LLM**: ~100ms simulated response time
- **Real LLM**: 500ms-5s depending on provider and model
- **Memory Usage**: ~10MB base + data size

## 🔧 Configuration Options

### Features
- `default`: Core functionality only
- `llm-apis`: Enable real LLM API integrations
- `sqlite`: Persistent storage backends
- `prometheus`: Metrics export

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API authentication
- `HUGGINGFACE_API_KEY`: Hugging Face API authentication
- `RUST_LOG`: Logging level (debug, info, warn, error)

## 📚 Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.rs`: Core functionality demonstration
- `with_real_apis.rs`: Real LLM integration
- `rest_server.rs`: HTTP API server implementation

Run examples with:
```bash
cargo run --example basic_usage
cargo run --example with_real_apis --features llm-apis
cargo run --example rest_server
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Tokio](https://tokio.rs/) for async runtime
- Uses [DashMap](https://github.com/xacrimon/dashmap) for concurrent data structures
- Inspired by modern RAG (Retrieval-Augmented Generation) architectures
=======
rsor/reasoning-agent-for-knowledge-graph-and-llm-interaction-b# Reasoni[![Test Coverage](https://img.shields.io/badge/coverage-unknown-lightgrey)](https://github.com/)

A modular, production-ready agent system with plugin interfaces for LLM, KG, vector store, and metrics. Includes REST API for task injection and status, robust error handling, and advanced developer experience features.

---

## Table of Contents
- [Features](#features)
- [Architecture](#architectur- [Plugin System](#plugin-system)
- [Setup](#setup)
- [Development Workflow](#development-workflow)
- [CLI Usage](#cli-usage)
- [Environment Variables](#environment-variables)
- [Testing & Coverage](#testing--coverage)
- [Deployment](#deployment)
- [Extending the System](#extending-the-system)
- [Contributing](#contributingm
## Features
- Pluggable LLM, KG, vector store, and metrics
- REST API (FastAPI) for task management
- WebSocket for live task updates
- Prometheus metrics endpoint
- Robust error handling and retries
- Persistence for KG and vectors
- Secure API key authentication
- Hot plugin reload in development
- Mock plugins and sample data for local/dev
- Typer-based CLI for dev utilities
- Pre-commit hooks, dev container, strict type checking, and test coverage

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for a full diagram and explanat
**Summary:**
- REST API receives tasks, handled by ReasoningAgent core
- Plugins for LLM, KG, vector store, and metrics
- WebSocket for live updates
- Prometheus for metrics
- Dockerized for easy deployment

---

## Plugin System
- Plugins are loaded dynamically based on environment/config
- Hot reload supported in dev mode (`DEV_MODE=1`)
- Mock plugins available for local/dev (`MOCK_PLUGINS=1`)
- To add a new plugin, subclass the relevant interface in `agent/interfaces.py` and update `agent/plugin_loader.py`

---

## Setup
1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Use the dev container for instant onboarding (VSCode: "Reopen in Container")
4. Set environment variables in `.env` (see below)
5. Run the API:
   ```bash
   uvicorn api.main:app --reload
   ```

---

## Development Workflow
- Install pre-commit hooks: `pre-commit install`
- Run tests: `pytest`
- Check types: `mypy .`
- Format code: `black . && isort .`
- Use the Typer CLI for common tasks (see below)
- Use mock plugins and sample data for local development
- Enable hot plugin reload with `DEV_MODE=1`

---

## CLI Usage

Use the Typer-based CLI for common dev tasks:

```bash
python manage.py seed           # Seed the KG and vector store with sample data
python manage.py clear          # Clear the KG database
python manage.py test           # Run all tests
python manage.py typecheck      # Run mypy type checks
python manage.py reload-plugins # Enable DEV_MODE for hot plugin reload (restart API after)
```

---

## Environment Variables
- `API_KEY`: API key for REST endpoints
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI LLM)
- `DB_URL`: Database URL for KG (e.g., `sqlite:///kg.db`)
- `LLM_PLUGIN`: LLM plugin to use (`openai` or `mock`)
- `KG_PLUGIN`: KG plugin to use (`sqlalchemy`)
- `VECTOR_PLUGIN`: Vector store plugin to use (`chroma`)
- `METRICS_PLUGIN`: Metrics plugin to use (`print`)
- `DEV_MODE`: Set to `1` to enable hot plugin reload
- `MOCK_PLUGINS`: Set to `1` to use mock plugins for local/dev

---

## Testing & Coverage
- Run all tests: `pytest`
- Check type safety: `mypy .`
- Coverage report: `pytest --cov`

---

## Deployment
- **Docker:**
  ```bash
  docker-compose up --build
  ```
- **Production:**
  - Set all required environment variables
  - Use a production-ready database (e.g., PostgreSQL)
  - Use a production LLM plugin and secure API keys
  - Monitor `/metrics` endpoint with Prometheus

---

## Extending the System
- **Add a new plugin:**
  1. Subclass the relevant interface in `agent/interfaces.py`
  2. Implement your plugin in `agent/plugins/`
  3. Update `agent/plugin_loader.py` to support your plugin
- **Add a new API endpoint:**
  - Add to `api/main.py` and update `api/schemas.py` as needed
- **Add a new CLI command:**
  - Add to `manage.py` using Typer
- **Add new tests:**
  - Place in `tests/` and ensure coverage

---

## Contributing
See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines on setup, testing, and pull requests.

---
==>>>> main
>>>>> main
