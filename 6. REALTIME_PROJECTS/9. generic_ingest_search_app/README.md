# Generic Ingest & Search Application

Full-stack application for ingesting data from various file formats into OpenSearch and performing advanced searches with AI-powered Plan-Execute-Reflect agents.

## 🎯 Features

### Ingestion
- ✅ Support for multiple file formats: **CSV**, **XLSX**, **JSONL**
- ✅ Multi-sheet Excel file handling with sheet selection
- ✅ Live data preview before ingestion
- ✅ Automatic pandas to OpenSearch data type mapping
- ✅ User-configurable field type overrides
- ✅ Optional **KNN vector embeddings** for semantic search
- ✅ Multiple pre-deployed sentence transformer models
- ✅ Real-time ingestion progress with detailed logging
- ✅ Comprehensive error handling with stack traces

### Search
- ✅ **Search-as-you-type**: Real-time prefix matching
- ✅ **Semantic Search**: Vector similarity using KNN
- ✅ **Hybrid Search**: Combined keyword + semantic search
- ✅ **AI-powered search** with Plan-Execute-Reflect agents (OpenAI GPT)
- ✅ Rich result display with scores and full document data

### Architecture
- ✅ **FastAPI** backend with async support
- ✅ **React** frontend with Material-UI
- ✅ **OpenSearch** for document storage and search
- ✅ **Redis** for session management and caching
- ✅ **Docker Compose** for one-command deployment
- ✅ JWT authentication with demo users

## 📋 Prerequisites

- Docker and Docker Compose
- (Optional) OpenAI API key for Plan-Execute-Reflect agent features

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
cd "6. REALTIME_PROJECTS/9. generic_ingest_search_app"
```

### 2. Configure Environment

```bash
# Copy example environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit .env and add your OpenAI API key (optional)
nano .env
```

### 3. Start the Stack

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **OpenSearch**: https://localhost:9200 (admin/Developer@123)

### 5. Login

Use one of the demo accounts:
- **Admin**: `admin` / `admin123`
- **User**: `user` / `user123`

## 📚 Usage Guide

### Ingestion Workflow

#### Step 1: Upload File
1. Click **"Start Ingestion"** from home page
2. Upload a CSV, XLSX, or JSONL file (max 50MB)
3. If XLSX with multiple sheets, select the sheet to ingest

#### Step 2: Preview Data
1. Review the first 10 rows
2. Check column names and detected data types
3. Click **"Next"** to proceed

#### Step 3: Configure Mappings
1. Review auto-detected OpenSearch field types
2. Modify types if needed (text, keyword, integer, float, date, etc.)
3. Click **"Next"**

#### Step 4: Select KNN Fields (Optional)
1. Choose which text fields should have vector embeddings
2. Select the sentence transformer model:
   - `all-MiniLM-L6-v2` (384 dims, faster)
   - `all-mpnet-base-v2` (768 dims, more accurate)
3. Click **"Next"**

#### Step 5: Review Summary
1. Review all configurations
2. Enter the **index name** (lowercase, alphanumeric with `-` or `_`)
3. Click **"Ingest"**

#### Step 6: Ingestion Progress
1. Watch real-time progress updates
2. See detailed logs from backend
3. View success message with document count
4. Choose to ingest more or start searching

### Search Workflow

#### Search-as-you-type
1. Select an index
2. Choose **"Search-as-you-type"**
3. Start typing in the query field
4. See instant results on every keystroke

#### Semantic Search
1. Select an index with KNN fields
2. Choose **"Semantic Search"**
3. Enter your natural language query
4. Click **"Search"**
5. Results ranked by vector similarity

#### Hybrid Search
1. Select an index with KNN fields
2. Choose **"Hybrid Search"**
3. Enter your query
4. Click **"Search"**
5. Results combine keyword matching + semantic similarity

## 🏗️ Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed Mermaid diagrams showing:
- System architecture
- Ingestion workflow
- Search flow
- Data type mapping
- Component interactions

## 🛠️ Technology Stack

### Backend
- **FastAPI** 0.115.5 - Modern async Python web framework
- **OpenSearch** 2.11.0 - Search and analytics engine
- **Redis** 7 - Caching and session storage
- **Pandas** 2.2.3 - Data manipulation
- **Pydantic** 2.10.3 - Data validation
- **Python** 3.12.11 with `uv` package manager

### Frontend
- **React** 18.3.1 - UI library
- **Material-UI** 6.1.9 - Component library
- **Axios** 1.7.9 - HTTP client
- **React Router** 6.28.0 - Navigation

### DevOps
- **Docker & Docker Compose** - Containerization
- **Uvicorn** - ASGI server
- **Node.js** 18 - Frontend build tools

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py          # Configuration management
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models
│   │   ├── routes/
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── ingest.py          # Ingestion endpoints
│   │   │   └── search.py          # Search endpoints
│   │   ├── services/
│   │   │   ├── opensearch_service.py   # OpenSearch client
│   │   │   ├── embedding_service.py    # ML model management
│   │   │   ├── file_service.py         # File processing
│   │   │   ├── ingest_service.py       # Ingestion logic
│   │   │   └── search_service.py       # Search with agents
│   │   └── utils/
│   ├── main.py                    # FastAPI app entry point
│   ├── pyproject.toml             # Python dependencies (uv)
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── ingest/            # Ingestion step components
│   │   ├── pages/
│   │   │   ├── Login.js           # Login page
│   │   │   ├── Home.js            # Dashboard
│   │   │   ├── IngestWorkflow.js  # Multi-step ingestion
│   │   │   └── Search.js          # Search interface
│   │   ├── services/
│   │   │   └── api.js             # API client
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json               # Node dependencies
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml             # Service orchestration
├── .env.example
├── ARCHITECTURE.md                # Mermaid diagrams
└── README.md                      # This file
```

## 🔧 Development

### Backend Development

```bash
cd backend

# Install dependencies with uv
uv pip install -r pyproject.toml

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v

# Rebuild specific service
docker-compose up -d --build backend

# Execute command in container
docker-compose exec backend bash
```

## 🧪 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Ingestion
- `POST /api/ingest/upload` - Upload file
- `POST /api/ingest/preview` - Preview data
- `POST /api/ingest/suggest-mappings` - Get suggested mappings
- `POST /api/ingest/confirm-mappings` - Confirm mappings
- `GET /api/ingest/available-models` - List embedding models
- `POST /api/ingest/confirm-knn` - Confirm KNN selections
- `POST /api/ingest/ingest-summary` - Get ingestion summary
- `POST /api/ingest/ingest` - Start ingestion

### Search
- `GET /api/search/indices` - List available indices
- `POST /api/search/execute` - Execute search
- `POST /api/search/execute-with-agent` - Execute with AI agent

## 📊 Data Type Mapping

| Pandas Type | OpenSearch Type |
|-------------|-----------------|
| int64, int32 | long / integer |
| float64, float32 | double / float |
| object | text (with keyword sub-field) |
| bool | boolean |
| datetime64 | date |

## 🔐 Security Notes

**⚠️ For Production Use:**

1. Change default passwords in `.env`:
   - `OPENSEARCH_PASSWORD`
   - `SECRET_KEY`

2. Enable SSL/TLS for OpenSearch

3. Use proper authentication (not demo users)

4. Set `DEBUG=false` in backend

5. Configure CORS properly

6. Use environment-specific `.env` files

## 🐛 Troubleshooting

### OpenSearch fails to start
- Increase Docker memory to at least 4GB
- Check `vm.max_map_count`: `sudo sysctl -w vm.max_map_count=262144`

### Backend can't connect to OpenSearch
- Wait for OpenSearch health check to pass
- Check `docker-compose logs opensearch`

### Redis connection errors
- Ensure Redis container is healthy
- Check network connectivity

### Frontend can't reach backend
- Verify `REACT_APP_API_URL` in frontend `.env`
- Check CORS settings in backend

### Embedding models fail to deploy
- Increase OpenSearch memory
- Check ML plugin is enabled
- View logs: `docker-compose logs backend`

## 📝 License

This project is part of the OpenSearch Intermediate Tutorial series.

## 🤝 Contributing

This is an educational project. Feel free to fork and extend!

## 📧 Support

For issues and questions, refer to the course materials or create an issue in the repository.

---

## 🎓 Learning Resources

### Key Concepts Demonstrated

1. **Full-stack development** with FastAPI + React
2. **OpenSearch ingestion pipelines** with text embeddings
3. **KNN vector search** for semantic similarity
4. **Plan-Execute-Reflect agents** for intelligent search
5. **Docker containerization** and orchestration
6. **RESTful API design** with OpenAPI/Swagger
7. **JWT authentication** and security
8. **Real-time progress streaming** with SSE
9. **Data type conversion** (Pandas ↔ OpenSearch)
10. **Multi-step form workflows** in React

### Advanced Topics Covered

- Ingest pipeline creation with text_embedding processor
- Hybrid search combining keyword + semantic approaches
- Agent-based search with OpenAI GPT models
- Asynchronous service initialization
- Redis caching for temporary data
- Docker health checks and service dependencies
- Material-UI component composition
- Axios interceptors for auth

---

**🎉 Happy Ingesting and Searching!**
