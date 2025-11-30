# MCP Client Documentation (`mcp_client.py`)

## 📋 Overview

The `mcp_client.py` module provides a sophisticated wrapper around the OpenSearch MCP (Model Context Protocol) server, enabling natural language interactions with OpenSearch through an AI agent powered by OpenAI's GPT models.

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Application Layer"
        A[Gradio App] -->|Uses| B[execute_query]
    end
    
    subgraph "MCP Client Module"
        B -->|Calls| C[get_mcp_client]
        C -->|Returns| D[MCPClient Singleton]
        D -->|Contains| E[ChatOpenAI LLM]
        D -->|Contains| F[MultiServerMCPClient]
        D -->|Contains| G[MCP Tools List]
    end
    
    subgraph "External Services"
        E -->|API Calls| H[OpenAI GPT-4]
        F -->|SSE Connection| I[MCP Server]
        I -->|REST API| J[OpenSearch Cluster]
    end
    
    style A fill:#4CAF50,color:#fff
    style D fill:#2196F3,color:#fff
    style E fill:#FF9800,color:#fff
    style F fill:#9C27B0,color:#fff
    style G fill:#00BCD4,color:#fff
    style H fill:#F44336,color:#fff
    style I fill:#FF5722,color:#fff
    style J fill:#795548,color:#fff
```

## 🔄 Singleton Pattern Implementation

```mermaid
sequenceDiagram
    participant App
    participant get_mcp_client
    participant MCPClient
    participant _mcp_client_global
    
    App->>get_mcp_client: First Call
    get_mcp_client->>_mcp_client_global: Check if exists
    _mcp_client_global-->>get_mcp_client: None
    get_mcp_client->>MCPClient: Create new instance
    MCPClient->>MCPClient: __new__() checks _instance
    MCPClient->>MCPClient: __init__() sets _initialized
    MCPClient->>MCPClient: initialize() async
    MCPClient-->>get_mcp_client: Return initialized client
    get_mcp_client->>_mcp_client_global: Store instance
    get_mcp_client-->>App: Return client
    
    App->>get_mcp_client: Second Call
    get_mcp_client->>_mcp_client_global: Check if exists
    _mcp_client_global-->>get_mcp_client: Existing instance
    get_mcp_client-->>App: Return cached client
```

### Why Singleton?

- **Resource Efficiency**: Maintains single connection to MCP server
- **State Preservation**: Keeps tools loaded across multiple queries
- **Connection Pooling**: Reuses OpenAI API client
- **Memory Optimization**: Prevents duplicate heavy objects

## 🚀 Initialization Flow

```mermaid
flowchart TD
    Start([App Starts]) --> GetClient[Call get_mcp_client]
    GetClient --> CheckGlobal{Global instance exists?}
    
    CheckGlobal -->|No| CreateInstance[Create MCPClient]
    CheckGlobal -->|Yes| ReturnExisting[Return existing instance]
    
    CreateInstance --> InitLLM[Initialize ChatOpenAI]
    InitLLM --> SetModel[Set model: gpt-4]
    SetModel --> SetTemp[Set temperature: 0]
    SetTemp --> SetKey[Set API key from config]
    
    SetKey --> InitMCPClient[Initialize MultiServerMCPClient]
    InitMCPClient --> ConfigureTransport[Configure SSE transport]
    ConfigureTransport --> SetURL[Set MCP server URL]
    
    SetURL --> LoadTools[Load tools from MCP server]
    LoadTools --> ToolsReady{Tools loaded?}
    
    ToolsReady -->|Yes| Success[Return Success: True]
    ToolsReady -->|No| Error[Return Success: False]
    
    Success --> ReturnClient[Return initialized client]
    Error --> RaiseError[Raise RuntimeError]
    ReturnExisting --> End([Ready for queries])
    ReturnClient --> End
    
    style Start fill:#4CAF50,color:#fff
    style CreateInstance fill:#2196F3,color:#fff
    style InitLLM fill:#FF9800,color:#fff
    style InitMCPClient fill:#9C27B0,color:#fff
    style LoadTools fill:#00BCD4,color:#fff
    style Success fill:#4CAF50,color:#fff
    style Error fill:#F44336,color:#fff
    style End fill:#4CAF50,color:#fff
```

## 🤖 Query Execution Flow (Agent Loop)

```mermaid
flowchart TD
    Start([User asks question]) --> ProcessQuery[execute_query called]
    ProcessQuery --> GetClient[Get MCPClient instance]
    GetClient --> CallQuery[client.query method]
    
    CallQuery --> ValidateClient{Client initialized?}
    ValidateClient -->|No| ReturnError[Return error: Not initialized]
    ValidateClient -->|Yes| BindTools[Bind tools to LLM]
    
    BindTools --> CreateMessages[Create message list]
    CreateMessages --> AddSystem[Add system prompt]
    AddSystem --> AddUser[Add user question]
    
    AddUser --> StartLoop[Initialize iteration counter]
    StartLoop --> LoopCheck{iteration < max_iterations?}
    
    LoopCheck -->|No| MaxReached[Return: Max iterations reached]
    LoopCheck -->|Yes| InvokeLLM[Invoke LLM with messages]
    
    InvokeLLM --> CheckToolCalls{LLM wants to use tools?}
    
    CheckToolCalls -->|No| FinalAnswer[Extract final answer]
    FinalAnswer --> ReturnSuccess[Return success with result]
    
    CheckToolCalls -->|Yes| IterateTools[For each tool_call]
    IterateTools --> ExtractTool[Extract tool name & args]
    ExtractTool --> FindTool[Find tool in tools list]
    FindTool --> ExecuteTool[Execute tool.ainvoke]
    
    ExecuteTool --> HandleResult{Tool execution success?}
    HandleResult -->|Yes| StoreResult[Store tool result]
    HandleResult -->|No| StoreError[Store error message]
    
    StoreResult --> AddToMessages[Add assistant + tool messages]
    StoreError --> AddToMessages
    AddToMessages --> MoreTools{More tools to call?}
    
    MoreTools -->|Yes| IterateTools
    MoreTools -->|No| IncrementIter[Increment iteration]
    IncrementIter --> LoopCheck
    
    ReturnSuccess --> End([Return to app])
    ReturnError --> End
    MaxReached --> End
    
    style Start fill:#4CAF50,color:#fff
    style InvokeLLM fill:#2196F3,color:#fff
    style ExecuteTool fill:#FF9800,color:#fff
    style ReturnSuccess fill:#4CAF50,color:#fff
    style ReturnError fill:#F44336,color:#fff
    style MaxReached fill:#FF5722,color:#fff
    style End fill:#4CAF50,color:#fff
```

## 🔧 Tool Management

```mermaid
graph TB
    subgraph "Tool Information Methods"
        A[get_tools_info] --> B[Iterate all tools]
        B --> C[Extract name & description]
        C --> D[Categorize with _categorize_tool]
        D --> E[Return tools_info list]
        
        F[get_tools_by_category] --> G[Call get_tools_info]
        G --> H[Group by category]
        H --> I[Return categorized dict]
    end
    
    subgraph "Tool Categories"
        D --> J1[Index Management]
        D --> J2[Document Operations]
        D --> J3[Search & Query]
        D --> J4[Cluster Management]
        D --> J5[Alias Management]
        D --> J6[Data Streams]
        D --> J7[Advanced]
    end
    
    style A fill:#2196F3,color:#fff
    style F fill:#9C27B0,color:#fff
    style J1 fill:#4CAF50,color:#fff
    style J2 fill:#FF9800,color:#fff
    style J3 fill:#00BCD4,color:#fff
    style J4 fill:#F44336,color:#fff
    style J5 fill:#9C27B0,color:#fff
    style J6 fill:#FF5722,color:#fff
    style J7 fill:#795548,color:#fff
```

## 💬 Message Flow in Agent Loop

```mermaid
sequenceDiagram
    participant User
    participant App
    participant MCPClient
    participant LLM as GPT-4
    participant Tool as MCP Tool
    participant OpenSearch
    
    User->>App: "List all indices"
    App->>MCPClient: execute_query(question)
    MCPClient->>MCPClient: Create messages array
    
    Note over MCPClient: Initial messages:<br/>[System, User]
    
    MCPClient->>LLM: Invoke with messages
    LLM->>LLM: Analyze question
    LLM-->>MCPClient: Response with tool_calls
    
    Note over MCPClient: tool_calls: [{<br/>name: "list_indices",<br/>args: {}<br/>}]
    
    MCPClient->>Tool: ainvoke(args)
    Tool->>OpenSearch: GET /_cat/indices
    OpenSearch-->>Tool: Indices data
    Tool-->>MCPClient: Tool result
    
    Note over MCPClient: Append messages:<br/>[Assistant, Tool]
    
    MCPClient->>LLM: Invoke with updated messages
    LLM->>LLM: Process tool result
    LLM-->>MCPClient: Natural language answer
    
    Note over MCPClient: No more tool_calls
    
    MCPClient-->>App: Return success + answer
    App-->>User: Display formatted result
```

## 📊 Data Structures

### MCPClient Class Attributes

```mermaid
classDiagram
    class MCPClient {
        -_instance: MCPClient
        -_initialized: bool
        +settings: Settings
        +client: MultiServerMCPClient
        +llm: ChatOpenAI
        +tools: List
        +agent: Any
        
        +__new__() MCPClient
        +__init__() None
        +initialize() bool
        +query(question, verbose) Dict
        +get_tools_info() List
        +_categorize_tool(tool_name) str
        +get_tools_by_category() Dict
        +close() None
    }
    
    class MultiServerMCPClient {
        +get_tools() List
    }
    
    class ChatOpenAI {
        +model: str
        +temperature: float
        +api_key: str
        +bind_tools(tools) ChatOpenAI
        +ainvoke(messages) AIMessage
    }
    
    MCPClient --> MultiServerMCPClient
    MCPClient --> ChatOpenAI
    
    style MCPClient fill:#2196F3,color:#fff
    style MultiServerMCPClient fill:#FF9800,color:#fff
    style ChatOpenAI fill:#4CAF50,color:#fff
```

### Query Response Format

```json
{
  "success": true,
  "result": "Natural language answer from GPT-4",
  "error": null,
  "metadata": {
    "tool_calls": [
      {
        "tool": "list_indices",
        "args": {},
        "result": "Index data..."
      }
    ],
    "iterations": 2
  }
}
```

## 🎯 Key Features

### 1. **Asynchronous Operations**
- All I/O operations use `async`/`await`
- Non-blocking tool execution
- Efficient resource utilization

### 2. **Error Handling**
```mermaid
graph LR
    A[Query Execution] --> B{Try Block}
    B -->|Success| C[Return result dict]
    B -->|Exception| D[Catch exception]
    D --> E[Format error message]
    E --> F[Add traceback]
    F --> G[Return error dict]
    
    style A fill:#2196F3,color:#fff
    style C fill:#4CAF50,color:#fff
    style D fill:#FF9800,color:#fff
    style G fill:#F44336,color:#fff
```

### 3. **Tool Categorization**
Automatically categorizes tools based on naming patterns:
- `*index*` → Index Management
- `*document*`, `*query*` → Document Operations
- `*search*` → Search & Query
- `*cluster*`, `*health*` → Cluster Management
- `*alias*` → Alias Management
- `*stream*` → Data Streams
- Default → Advanced

### 4. **Verbose Mode**
When enabled, prints real-time tool execution details:
```
🔧 Calling tool: search_documents
   Args: {'index': 'ecommerce', 'body': {...}}
```

## 🔐 Security Considerations

```mermaid
graph TD
    A[API Keys] --> B[Loaded from .env]
    B --> C[Never hardcoded]
    C --> D[Settings class]
    
    E[MCP Connection] --> F[Local SSE transport]
    F --> G[No external exposure]
    
    H[OpenSearch Connection] --> I[Through MCP server]
    I --> J[Credential isolation]
    
    style A fill:#F44336,color:#fff
    style E fill:#FF9800,color:#fff
    style H fill:#2196F3,color:#fff
```

## 📈 Performance Optimization

### Singleton Benefits
- **Connection Reuse**: Single MCP client instance
- **Tool Caching**: Tools loaded once at initialization
- **Memory Efficiency**: Prevents object duplication

### Async Benefits
- **Non-blocking I/O**: Multiple queries can be processed concurrently
- **Responsive UI**: Gradio interface remains responsive during queries
- **Efficient Resource Usage**: Better CPU utilization

## 🧪 Usage Examples

### Basic Query
```python
from mcp_client import execute_query

result = await execute_query("List all indices")
print(result['result'])
```

### Verbose Query
```python
result = await execute_query(
    "Find orders over $100", 
    verbose=True
)
```

### Get Tools Information
```python
from mcp_client import get_mcp_client

client = await get_mcp_client()
tools = client.get_tools_info()
categorized = client.get_tools_by_category()
```

## 🔄 Lifecycle Management

```mermaid
stateDiagram-v2
    [*] --> Uninitialized
    Uninitialized --> Initializing: get_mcp_client()
    Initializing --> Ready: initialize() success
    Initializing --> Error: initialize() failure
    
    Ready --> Processing: query()
    Processing --> Ready: Success
    Processing --> Error: Exception
    
    Error --> Initializing: Retry
    Ready --> Closed: close()
    Closed --> [*]
    
    note right of Ready
        Can handle multiple
        concurrent queries
    end note
```

## 🐛 Troubleshooting

### Common Issues

1. **"MCP client not initialized"**
   - Ensure MCP server is running
   - Check `mcp_server_url` in config
   - Verify network connectivity

2. **"Max iterations reached"**
   - Query too complex
   - Tool execution failures
   - LLM stuck in loop

3. **Tool execution errors**
   - OpenSearch connection issues
   - Invalid query parameters
   - Missing index or documents

## 📚 Related Files

- `config.py` - Settings and configuration
- `start_mcp_server.py` - MCP server startup script
- `app.py` - Gradio application using this client

---

**Version**: 1.0  
**Last Updated**: 2025-11-30  
**Maintainer**: OpenSearch MCP Demo Team
