# OpenSearch Course Catalog

## Overview
This catalog provides a comprehensive, searchable index of all course materials in the OpenSearch Intermediate Tutorial repository. Each file has been deeply analyzed and tagged with relevant concepts, acronyms, and semantic keywords to help students quickly find the right learning materials.

## Generated File
**Filename:** `course_catalog_opensearch.jsonl`  
**Format:** OpenSearch-compatible JSONL (newline-delimited JSON)  
**Total Entries:** 248 files  
**Total Lines:** 496 (248 index actions + 248 documents)

## Catalog Structure
Each entry contains:
- **module**: Top-level folder (e.g., "5. AGENTIC_SEARCH")
- **sub_module**: Subfolder within the module (e.g., "5. agents_tools")
- **filename**: Name of the file
- **associated_markdown_file**: Related documentation (if any)
- **tags**: Comprehensive list of searchable keywords (average 39 tags per file)
- **file_path**: Relative path from repository root
- **file_type**: File extension (py, ipynb, md, yml, etc.)

## Statistics

### Files by Module
- **1. INSTALLATION_CONFIGURATION**: 5 files
- **2. TRADITIONAL_SEARCH**: 8 files
- **3. INGEST_AND_SEARCH_CONCEPTS**: 48 files
- **4. AI_SEARCH**: 6 files
- **5. AGENTIC_SEARCH**: 95 files
- **6. REALTIME_PROJECTS**: 85 files
- **helpers.py**: 1 file

### Files by Type
- **Python scripts (.py)**: 67 files
- **Jupyter notebooks (.ipynb)**: 37 files
- **Markdown documentation (.md)**: 103 files
- **YAML configs (.yml)**: 28 files
- **YAML configs (.yaml)**: 7 files
- **Docker files (.dockerfile)**: 6 files

### Tag Statistics
- **Total unique tags**: 422
- **Average tags per file**: 39.0
- **Unique acronyms**: 25 (BM25, KNN, RAG, LLM, MMR, etc.)
- **Multi-word concepts**: 84 (semantic search, hybrid search, etc.)

## Top Tags
1. opensearch basics (220 files)
2. opensearch (210 files)
3. mcp (163 files)
4. applications (157 files)
5. api / API (146 files)
6. cluster (144 files)
7. index (141 files)
8. ml models (139 files)
9. security (139 files)
10. client (136 files)

## Tag Categories

### Search & Retrieval
- keyword search, full-text search, semantic search, hybrid search
- vector search, neural search, neural sparse search
- bm25, knn, hnsw, cosine similarity, reciprocal rank fusion (rrf)
- mmr (maximal marginal relevance)

### Machine Learning & Models
- sentence transformer, bert, distilbert, roberta, gpt
- all-minilm, msmarco, mpnet
- onnx, torchscript, ml commons

### Data Processing
- ingest pipeline, search pipeline, processor
- bulk ingestion, batch processing, streaming
- data prepper, otel (opentelemetry)

### Vector Operations
- dense vector, sparse vector, embeddings
- knn, hnsw (hierarchical navigable small world)
- ivf (inverted file index), faiss, nmslib

### AI & Agents
- rag (retrieval augmented generation)
- llm (large language model), agent, tool
- function calling, reasoning, plan-execute-reflect
- openai, anthropic, ollama, deepseek

### Infrastructure
- docker, docker-compose, cluster, nodes
- jvm, heap, performance, optimization
- security, ssl/tls, authentication

## How to Use

### 1. Ingest into OpenSearch
```bash
curl -X POST 'localhost:9200/_bulk' \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @course_catalog_opensearch.jsonl
```

### 2. Search for Topics
```bash
# Find all files about hybrid search
curl -X GET "localhost:9200/course_catalog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "tags": "hybrid search"
    }
  }
}'

# Find files by module
curl -X GET "localhost:9200/course_catalog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "module.keyword": "5. AGENTIC_SEARCH"
    }
  }
}'

# Find by acronym (e.g., RAG, MMR, KNN)
curl -X GET "localhost:9200/course_catalog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "tags": "MMR"
    }
  }
}'
```

### 3. Filter by File Type
```bash
# Find all Jupyter notebooks
curl -X GET "localhost:9200/course_catalog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "file_type": "ipynb"
    }
  }
}'
```

## Example Use Cases

### Student: "I want to learn about reranking"
Search tags: `rerank`, `mmr`, `rrf`, `cross encoder`, `reciprocal rank fusion`

### Student: "Show me practical agent implementations"
Filter: `module: "5. AGENTIC_SEARCH"` + `sub_module: "5. agents_tools"` + `file_type: "py"`

### Student: "I need help with vector search performance"
Search tags: `hnsw`, `performance`, `optimization`, `vectors embeddings`

### Student: "How do I set up OpenSearch with Docker?"
Filter: `module: "1. INSTALLATION_CONFIGURATION"` + search tags: `docker compose`

## Generation Details

### Excluded Patterns
- `.venv/` folders (virtual environments)
- `__pycache__/` folders (Python cache)
- `.egg-info/` folders (package metadata)
- `node_modules/` folders (Node.js dependencies)

### Tag Extraction Methods
1. **Syntax-based**: Pattern matching for OpenSearch APIs, queries, configuration
2. **Semantic**: Concept extraction from documentation and code comments
3. **Acronyms**: Full expansion provided (e.g., MMR → Maximal Marginal Relevance)
4. **Filename**: Keywords extracted from file and folder names
5. **Deep content**: Analysis of Python functions, notebook cells, markdown headers

## Maintenance
To regenerate the catalog after adding new files:
```bash
python generate_course_catalog.py
```

## Schema Example
```json
{
  "index": {"_index": "course_catalog", "_id": 0}
}
{
  "module": "5. AGENTIC_SEARCH",
  "sub_module": "5. agents_tools",
  "filename": "4. plan_execute_reflect_agent.py",
  "associated_markdown_file": "4. plan_execute_reflect_agent.md",
  "tags": ["agent", "plan-execute", "reflect", "reasoning", "rag", "llm", "openai", "ollama", ...],
  "file_path": "5. AGENTIC_SEARCH/5. agents_tools/4. plan_execute_reflect_agent.py",
  "file_type": "py"
}
```

---
