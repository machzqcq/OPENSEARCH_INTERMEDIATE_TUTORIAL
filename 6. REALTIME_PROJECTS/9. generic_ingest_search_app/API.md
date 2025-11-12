# API Documentation

Complete REST API reference for the Generic Ingest & Search application.

**Base URL**: `http://localhost:8000`

**Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)

## 🔐 Authentication

All endpoints (except `/api/auth/login`) require JWT authentication.

### Headers
```
Authorization: Bearer <access_token>
```

---

## 📌 Authentication Endpoints

### POST /api/auth/login

Login and receive JWT access token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "username": "admin",
  "email": "admin@example.com"
}
```

**Demo Users:**
- Admin: `admin` / `admin123`
- User: `user` / `user123`

### GET /api/auth/me

Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "username": "admin",
  "email": "admin@example.com"
}
```

### POST /api/auth/logout

Logout (token invalidation handled client-side).

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

## 📥 Ingestion Endpoints

### POST /api/ingest/upload

Upload data file (CSV, XLSX, JSONL).

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/ingest/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv"
```

**Response (200 OK):**
```json
{
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "data.csv",
  "format": "csv",
  "sheets": null,
  "message": "File uploaded successfully"
}
```

For XLSX files:
```json
{
  "file_id": "uuid",
  "filename": "data.xlsx",
  "format": "xlsx",
  "sheets": ["Sheet1", "Sheet2", "Sales Data"],
  "message": "File uploaded successfully"
}
```

### POST /api/ingest/preview

Preview uploaded data.

**Request Body:**
```json
{
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sheet_name": "Sheet1"  // Optional, for XLSX only
}
```

**Response (200 OK):**
```json
{
  "columns": ["id", "name", "age", "city"],
  "data": [
    {"id": 1, "name": "John", "age": 30, "city": "NYC"},
    {"id": 2, "name": "Jane", "age": 25, "city": "LA"},
    ...
  ],
  "total_rows": 1000,
  "preview_rows": 10,
  "dtypes": {
    "id": "int64",
    "name": "object",
    "age": "int64",
    "city": "object"
  }
}
```

### POST /api/ingest/suggest-mappings

Get suggested OpenSearch field mappings.

**Request Body:**
```json
{
  "file_id": "uuid",
  "sheet_name": null
}
```

**Response (200 OK):**
```json
{
  "mappings": [
    {
      "column_name": "id",
      "opensearch_type": "long",
      "is_knn": false
    },
    {
      "column_name": "name",
      "opensearch_type": "text",
      "is_knn": false
    },
    {
      "column_name": "age",
      "opensearch_type": "long",
      "is_knn": false
    },
    {
      "column_name": "description",
      "opensearch_type": "text",
      "is_knn": false
    }
  ],
  "message": "Mappings suggested based on data types"
}
```

### POST /api/ingest/confirm-mappings

Confirm user-selected field mappings.

**Request Body:**
```json
{
  "file_id": "uuid",
  "mappings": [
    {
      "column_name": "id",
      "opensearch_type": "keyword",  // User changed from long
      "is_knn": false
    },
    {
      "column_name": "name",
      "opensearch_type": "text",
      "is_knn": false
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Mappings confirmed and stored",
  "file_id": "uuid"
}
```

### GET /api/ingest/available-models

Get list of deployed embedding models.

**Response (200 OK):**
```json
{
  "models": [
    {
      "model_id": "model_abc123",
      "name": "all-MiniLM-L6-v2",
      "dimension": 384,
      "description": "Fast and efficient for general semantic search",
      "status": "DEPLOYED"
    },
    {
      "model_id": "model_def456",
      "name": "all-mpnet-base-v2",
      "dimension": 768,
      "description": "Higher quality embeddings, slower but more accurate",
      "status": "DEPLOYED"
    }
  ]
}
```

### POST /api/ingest/confirm-knn

Confirm KNN column selections.

**Request Body:**
```json
{
  "file_id": "uuid",
  "knn_columns": [
    {
      "column_name": "description",
      "model_id": "model_abc123",
      "model_name": "all-MiniLM-L6-v2"
    },
    {
      "column_name": "title",
      "model_id": "model_abc123",
      "model_name": "all-MiniLM-L6-v2"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "KNN configuration stored for 2 columns",
  "selected_columns": ["description", "title"]
}
```

### POST /api/ingest/ingest-summary

Get ingestion summary for review.

**Request Body:**
```json
{
  "file_id": "uuid"
}
```

**Response (200 OK):**
```json
{
  "file_id": "uuid",
  "filename": "products.csv",
  "total_rows": 5000,
  "columns": ["id", "name", "description", "price"],
  "mappings": [...],
  "knn_columns": [...],
  "estimated_size": "5000 documents"
}
```

### POST /api/ingest/ingest

Start bulk ingestion.

**Request Body:**
```json
{
  "file_id": "uuid",
  "index_name": "my_products_index"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "index_name": "my_products_index",
  "documents_ingested": 5000,
  "pipeline_id": "my_products_index_pipeline",
  "elapsed_time": 45.23,
  "errors": null,
  "message": "Successfully ingested 5000 documents"
}
```

**Error Response (500):**
```json
{
  "success": false,
  "index_name": "my_products_index",
  "documents_ingested": 0,
  "errors": ["Index already exists"],
  "message": "Ingestion failed"
}
```

---

## 🔍 Search Endpoints

### GET /api/search/indices

Get list of available indices.

**Response (200 OK):**
```json
{
  "indices": [
    "my_products_index",
    "customer_data",
    "sales_records"
  ]
}
```

### POST /api/search/execute

Execute search query.

**Request Body:**
```json
{
  "index_name": "my_products_index",
  "query": "wireless headphones",
  "search_type": "search_as_you_type",
  "size": 10
}
```

**Search Types:**
- `search_as_you_type` - Real-time prefix matching
- `semantic` - Vector similarity search
- `hybrid` - Combined keyword + semantic

**Response (200 OK):**
```json
{
  "hits": [
    {
      "id": "1",
      "score": 4.523,
      "source": {
        "id": 1,
        "name": "Wireless Bluetooth Headphones",
        "description": "High-quality wireless headphones",
        "price": 79.99
      }
    },
    {
      "id": "5",
      "score": 3.891,
      "source": {
        "id": 5,
        "name": "USB-C Headphone Adapter",
        "description": "Connect your headphones",
        "price": 12.99
      }
    }
  ],
  "total": 24,
  "took": 15,
  "search_type": "search_as_you_type"
}
```

### POST /api/search/execute-with-agent

Execute search with Plan-Execute-Reflect AI agent.

**Request Body:**
```json
{
  "index_name": "my_products_index",
  "query": "What are the best affordable wireless accessories?",
  "search_type": "hybrid",
  "size": 10
}
```

**Response (200 OK):**
```json
{
  "hits": [...],
  "total": 15,
  "took": 234,
  "search_type": "hybrid",
  "agent_insights": "Based on the search results, the best affordable wireless accessories include..."
}
```

---

## 🌐 System Endpoints

### GET /

Root endpoint - health check.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "message": "Generic Ingest & Search API",
  "version": "1.0.0"
}
```

### GET /health

Detailed health check.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "opensearch": {
    "status": "green",
    "cluster_name": "opensearch-cluster",
    "number_of_nodes": 1
  }
}
```

**Error Response (503):**
```json
{
  "detail": "Service unhealthy: Connection refused"
}
```

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## 🔧 Error Format

All errors follow this format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "trace": ["Stack trace line 1", "Line 2", ...]
}
```

Example:
```json
{
  "error": "ValidationError",
  "detail": "Index name must be lowercase",
  "trace": null
}
```

---

## 💡 Usage Examples

### Complete Ingestion Flow

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 2. Upload file
FILE_ID=$(curl -X POST http://localhost:8000/api/ingest/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data.csv" \
  | jq -r '.file_id')

# 3. Preview data
curl -X POST http://localhost:8000/api/ingest/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\"}"

# 4. Get suggested mappings
curl -X POST http://localhost:8000/api/ingest/suggest-mappings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\"}"

# 5. Ingest
curl -X POST http://localhost:8000/api/ingest/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\",\"index_name\":\"test_index\"}"
```

### Search Flow

```bash
# Get indices
curl -X GET http://localhost:8000/api/search/indices \
  -H "Authorization: Bearer $TOKEN"

# Execute search
curl -X POST http://localhost:8000/api/search/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "test_index",
    "query": "search query",
    "search_type": "semantic",
    "size": 10
  }'
```

---

## 📚 Additional Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

**🎯 For more details, see the interactive API documentation at `/docs`**
