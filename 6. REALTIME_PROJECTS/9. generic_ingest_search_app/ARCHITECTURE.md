# Architecture and Flow Diagrams

This document contains colorful Mermaid diagrams explaining the system architecture and data flows.

## System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React App<br/>Port: 3000]
        A1[Login Page]
        A2[Home Dashboard]
        A3[Ingestion Workflow]
        A4[Search Interface]
        
        A --> A1
        A --> A2
        A --> A3
        A --> A4
    end
    
    subgraph "Backend Layer"
        B[FastAPI Server<br/>Port: 8000]
        B1[Auth Routes]
        B2[Ingest Routes]
        B3[Search Routes]
        B4[Services Layer]
        
        B --> B1
        B --> B2
        B --> B3
        B --> B4
    end
    
    subgraph "Data Layer"
        C[OpenSearch<br/>Port: 9200]
        C1[Document Storage]
        C2[Vector Index]
        C3[ML Models]
        C4[Agents]
        
        C --> C1
        C --> C2
        C --> C3
        C --> C4
    end
    
    subgraph "Cache Layer"
        D[Redis<br/>Port: 6379]
        D1[File Metadata]
        D2[Session Data]
        D3[Temp Storage]
        
        D --> D1
        D --> D2
        D --> D3
    end
    
    A -->|HTTP/REST API| B
    B -->|OpenSearch Client| C
    B -->|Redis Client| D
    
    style A fill:#61dafb,stroke:#333,stroke-width:3px,color:#000
    style B fill:#009688,stroke:#333,stroke-width:3px,color:#fff
    style C fill:#005eb8,stroke:#333,stroke-width:3px,color:#fff
    style D fill:#dc382d,stroke:#333,stroke-width:3px,color:#fff
```

## Ingestion Workflow

```mermaid
flowchart TD
    Start([User Logs In]) --> Upload[Step 1: Upload File<br/>CSV, XLSX, or JSONL]
    
    Upload -->|File Uploaded| Check{File Type?}
    
    Check -->|XLSX| Sheets[Select Sheet]
    Check -->|CSV/JSONL| Preview
    Sheets --> Preview
    
    Preview[Step 2: Preview Data<br/>Show first 10 rows<br/>Display columns & types]
    
    Preview --> Mapping[Step 3: Configure Mappings<br/>Auto-detect from pandas<br/>User can override]
    
    Mapping --> KNN{Add Vector<br/>Embeddings?}
    
    KNN -->|Yes| SelectModel[Step 4: Select KNN Columns<br/>Choose embedding model<br/>Select fields to embed]
    KNN -->|No| Review
    
    SelectModel --> Review[Step 5: Review Summary<br/>All configurations<br/>Enter index name]
    
    Review --> Confirm{User<br/>Confirms?}
    
    Confirm -->|No| Mapping
    Confirm -->|Yes| CreateIndex[Create Index<br/>with Mappings]
    
    CreateIndex --> Pipeline{KNN<br/>Enabled?}
    
    Pipeline -->|Yes| CreatePipeline[Create Ingest Pipeline<br/>with text_embedding processor]
    Pipeline -->|No| BulkIngest
    
    CreatePipeline --> BulkIngest[Step 6: Bulk Ingest<br/>Stream progress to UI<br/>Show log updates]
    
    BulkIngest --> Success{Ingest<br/>Success?}
    
    Success -->|Yes| Complete[Show Success<br/>Documents ingested<br/>Time elapsed]
    Success -->|No| Error[Show Error<br/>Stack trace<br/>Detailed logs]
    
    Complete --> Options{User<br/>Choice?}
    
    Options -->|Ingest More| Upload
    Options -->|Search| SearchPage[Navigate to Search]
    
    Error --> Retry{Retry?}
    Retry -->|Yes| Mapping
    Retry -->|No| End([End])
    
    SearchPage --> End
    
    style Start fill:#4caf50,stroke:#333,stroke-width:3px,color:#fff
    style Upload fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style Preview fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style Mapping fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style SelectModel fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style Review fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style BulkIngest fill:#ff9800,stroke:#333,stroke-width:2px,color:#000
    style Complete fill:#4caf50,stroke:#333,stroke-width:3px,color:#fff
    style Error fill:#f44336,stroke:#333,stroke-width:3px,color:#fff
    style End fill:#9e9e9e,stroke:#333,stroke-width:3px,color:#fff
```

## Search Flow

```mermaid
flowchart TD
    Start([User at Search Page]) --> SelectIndex[Select Index<br/>from dropdown]
    
    SelectIndex --> SelectType[Select Search Type]
    
    SelectType --> Type{Which Type?}
    
    Type -->|Search-as-you-type| SAYT[Real-time Search<br/>Match phrase prefix<br/>Instant results]
    Type -->|Semantic| Semantic[Semantic Search<br/>Vector similarity<br/>KNN search]
    Type -->|Hybrid| Hybrid[Hybrid Search<br/>Keyword + Vector<br/>Combined ranking]
    
    SAYT --> UserTypes{User<br/>Typing?}
    UserTypes -->|Yes| ExecuteSAYT[Execute Search<br/>on every keystroke]
    UserTypes -->|No| ExecuteSAYT
    
    Semantic --> UserEnters[User enters query<br/>Clicks Search]
    Hybrid --> UserEnters
    
    UserEnters --> UseAgent{Use AI<br/>Agent?}
    
    UseAgent -->|Yes| PER[Plan-Execute-Reflect<br/>Agent Processing]
    UseAgent -->|No| DirectSearch[Direct OpenSearch<br/>Query]
    
    PER --> Phase1[Phase 1: PLAN<br/>Analyze query<br/>Break into steps]
    Phase1 --> Phase2[Phase 2: EXECUTE<br/>Run search tools<br/>Collect results]
    Phase2 --> Phase3[Phase 3: REFLECT<br/>Evaluate completeness<br/>Refine if needed]
    
    Phase3 --> Results
    DirectSearch --> Results
    ExecuteSAYT --> Results
    
    Results[Display Results<br/>Score, ID, Fields<br/>Formatted cards]
    
    Results --> UserAction{User<br/>Action?}
    
    UserAction -->|New Search| SelectType
    UserAction -->|Go Home| Home[Navigate to Home]
    UserAction -->|Logout| Logout[User Logs Out]
    
    Home --> End([End])
    Logout --> End
    
    style Start fill:#4caf50,stroke:#333,stroke-width:3px,color:#fff
    style SAYT fill:#e91e63,stroke:#333,stroke-width:2px,color:#fff
    style Semantic fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff
    style Hybrid fill:#673ab7,stroke:#333,stroke-width:2px,color:#fff
    style PER fill:#ff9800,stroke:#333,stroke-width:3px,color:#000
    style Phase1 fill:#ffc107,stroke:#333,stroke-width:2px,color:#000
    style Phase2 fill:#ffc107,stroke:#333,stroke-width:2px,color:#000
    style Phase3 fill:#ffc107,stroke:#333,stroke-width:2px,color:#000
    style Results fill:#4caf50,stroke:#333,stroke-width:3px,color:#fff
    style End fill:#9e9e9e,stroke:#333,stroke-width:3px,color:#fff
```

## Data Type Mapping Flow

```mermaid
flowchart LR
    subgraph "Pandas DataFrame"
        P1[int64]
        P2[float64]
        P3[object]
        P4[bool]
        P5[datetime64]
    end
    
    subgraph "Conversion Logic"
        C[Type Mapper<br/>pandas_dtype_to_opensearch]
    end
    
    subgraph "OpenSearch Types"
        OS1[long]
        OS2[double]
        OS3[text + keyword]
        OS4[boolean]
        OS5[date]
    end
    
    subgraph "Optional KNN"
        K1[text field + <br/>knn_vector field<br/>dimension: 384/768]
    end
    
    P1 -->|Auto-detect| C
    P2 -->|Auto-detect| C
    P3 -->|Auto-detect| C
    P4 -->|Auto-detect| C
    P5 -->|Auto-detect| C
    
    C --> OS1
    C --> OS2
    C --> OS3
    C --> OS4
    C --> OS5
    
    OS3 -.->|User selects| K1
    
    style P1 fill:#4caf50,stroke:#333,stroke-width:2px
    style P2 fill:#4caf50,stroke:#333,stroke-width:2px
    style P3 fill:#4caf50,stroke:#333,stroke-width:2px
    style P4 fill:#4caf50,stroke:#333,stroke-width:2px
    style P5 fill:#4caf50,stroke:#333,stroke-width:2px
    style C fill:#ff9800,stroke:#333,stroke-width:3px
    style OS1 fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style OS2 fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style OS3 fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style OS4 fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style OS5 fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    style K1 fill:#9c27b0,stroke:#333,stroke-width:3px,color:#fff
```

## Component Interaction Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend<br/>(React)
    participant B as Backend<br/>(FastAPI)
    participant R as Redis
    participant O as OpenSearch
    
    Note over U,O: Authentication Flow
    U->>F: Enter credentials
    F->>B: POST /api/auth/login
    B->>B: Validate credentials
    B-->>F: JWT token
    F->>F: Store token
    F-->>U: Navigate to Home
    
    Note over U,O: Ingestion Flow
    U->>F: Upload file
    F->>B: POST /api/ingest/upload
    B->>R: Store file metadata
    B-->>F: file_id, sheets
    
    U->>F: Select sheet (if XLSX)
    F->>B: POST /api/ingest/preview
    B->>R: Load DataFrame info
    B-->>F: Preview data
    
    U->>F: Confirm mappings
    F->>B: POST /api/ingest/confirm-mappings
    B->>R: Store mappings
    
    U->>F: Select KNN columns
    F->>B: POST /api/ingest/confirm-knn
    B->>R: Store KNN config
    
    U->>F: Enter index name & ingest
    F->>B: POST /api/ingest/ingest
    B->>O: Create index with mappings
    B->>O: Create ingest pipeline (if KNN)
    B->>O: Bulk index documents
    B-->>F: Stream progress updates
    F-->>U: Show progress & logs
    
    Note over U,O: Search Flow
    U->>F: Enter search query
    F->>B: POST /api/search/execute
    B->>O: Execute search query
    O-->>B: Search results
    B-->>F: Formatted results
    F-->>U: Display results
```

---

## Color Legend

- 🟦 **Blue**: Core services and data processing
- 🟩 **Green**: Success states and start/end points
- 🟧 **Orange**: Processing and transformation steps
- 🟥 **Red**: Error states and warnings
- 🟪 **Purple**: Advanced features (AI/ML)
- 🟨 **Yellow**: Agent processing phases
- ⬜ **Gray**: End states and neutral actions
