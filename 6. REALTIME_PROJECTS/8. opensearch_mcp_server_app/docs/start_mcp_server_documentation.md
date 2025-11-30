# MCP Server Startup Script Documentation (`start_mcp_server.py`)

## 📋 Overview

The `start_mcp_server.py` script is a convenient helper utility that manages the lifecycle of the OpenSearch MCP (Model Context Protocol) server. It handles server initialization, health checks, port management, and graceful shutdown.

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "User Interaction"
        A[User runs script] -->|python start_mcp_server.py| B[Main Entry Point]
    end
    
    subgraph "Initialization Phase"
        B --> C[Get port from env]
        C --> D[start_mcp_server]
        D --> E[check_port_available]
        E --> F{Port available?}
    end
    
    subgraph "Configuration Phase"
        F -->|No| G[Prompt user]
        F -->|Yes| H[Load environment]
        G --> I{Continue?}
        I -->|No| J[Exit]
        I -->|Yes| H
        H --> K[Check config file]
    end
    
    subgraph "Server Launch"
        K --> L[Build subprocess command]
        L --> M[Start MCP server process]
        M --> N[Health check loop]
    end
    
    subgraph "Running State"
        N --> O{Server healthy?}
        O -->|Yes| P[Display ready message]
        O -->|No| Q[Retry or fail]
        P --> R[Wait for Ctrl+C]
    end
    
    subgraph "Shutdown"
        R --> S[KeyboardInterrupt]
        S --> T[Terminate process]
        T --> U[Clean exit]
    end
    
    style B fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
    style M fill:#FF9800,color:#fff
    style P fill:#4CAF50,color:#fff
    style T fill:#F44336,color:#fff
    style U fill:#4CAF50,color:#fff
```

## 🔄 Detailed Execution Flow

```mermaid
flowchart TD
    Start([Script Executed]) --> GetPort[Get port from env<br/>default: 9900]
    GetPort --> CallStart[Call start_mcp_server]
    
    CallStart --> PrintInfo[Print startup info]
    PrintInfo --> CheckPort[check_port_available]
    
    CheckPort --> HTTPRequest[Try GET /health endpoint]
    HTTPRequest --> PortCheck{Response received?}
    
    PortCheck -->|Yes| PortInUse[Port is in use]
    PortCheck -->|No| PortFree[Port is available]
    
    PortInUse --> AskUser[Prompt: Continue anyway?]
    AskUser --> UserChoice{User says yes?}
    UserChoice -->|No| Exit1[Exit gracefully]
    UserChoice -->|Yes| LoadEnv[Load environment]
    PortFree --> LoadEnv
    
    LoadEnv --> TryDotenv{python-dotenv installed?}
    TryDotenv -->|Yes| LoadDotenv[load_dotenv]
    TryDotenv -->|No| WarnNoDotenv[Warn: Use system env]
    
    LoadDotenv --> CheckConfig[Check for config.yaml]
    WarnNoDotenv --> CheckConfig
    
    CheckConfig --> ConfigExists{Config file exists?}
    ConfigExists -->|Yes| UseConfig[Include --config flag]
    ConfigExists -->|No| NoConfig[Skip config]
    
    UseConfig --> BuildCmd[Build subprocess command]
    NoConfig --> BuildCmd
    
    BuildCmd --> CreateList[Create command list]
    CreateList --> AddPython[sys.executable]
    AddPython --> AddModule[-m mcp_server_opensearch]
    AddModule --> AddTransport[--transport stream]
    AddTransport --> AddPort[--port 9900]
    AddPort --> AddConfigFlag{Using config?}
    AddConfigFlag -->|Yes| AddConfigPath[--config path/to/config.yaml]
    AddConfigFlag -->|No| StartProcess
    AddConfigPath --> StartProcess[subprocess.Popen]
    
    StartProcess --> ProcessStarted{Process started?}
    ProcessStarted -->|No| ErrorNotFound[Package not found error]
    ProcessStarted -->|Yes| PrintPID[Print PID]
    
    ErrorNotFound --> ShowInstall[Show pip install command]
    ShowInstall --> Exit2[Exit with code 1]
    
    PrintPID --> HealthLoop[Health check loop<br/>max 30 attempts]
    HealthLoop --> AttemptHealth[GET /health]
    AttemptHealth --> HealthCheck{Status 200?}
    
    HealthCheck -->|Yes| ServerReady[Print ready message]
    HealthCheck -->|No| Sleep1s[Sleep 1 second]
    Sleep1s --> CheckAttempts{More attempts?}
    CheckAttempts -->|Yes| AttemptHealth
    CheckAttempts -->|No| HealthFailed[Print warning]
    
    ServerReady --> WaitForInterrupt[process.wait]
    HealthFailed --> WaitForInterrupt
    
    WaitForInterrupt --> Interrupt{Ctrl+C pressed?}
    Interrupt -->|Yes| Terminate[process.terminate]
    Terminate --> WaitForExit[process.wait]
    WaitForExit --> PrintStopped[Print stopped message]
    PrintStopped --> Exit3[Exit gracefully]
    
    Interrupt -->|Process ended| Exit3
    
    style Start fill:#4CAF50,color:#fff
    style CheckPort fill:#2196F3,color:#fff
    style StartProcess fill:#FF9800,color:#fff
    style ServerReady fill:#4CAF50,color:#fff
    style ErrorNotFound fill:#F44336,color:#fff
    style Terminate fill:#FF5722,color:#fff
    style Exit3 fill:#4CAF50,color:#fff
```

## 🔍 Port Availability Check

```mermaid
sequenceDiagram
    participant Script
    participant check_port_available
    participant HTTP Client
    participant Port
    
    Script->>check_port_available: Check port 9900
    check_port_available->>HTTP Client: GET http://localhost:9900/health
    
    alt Port Available
        HTTP Client->>Port: Connection attempt
        Port-->>HTTP Client: Connection refused
        HTTP Client-->>check_port_available: Exception
        check_port_available-->>Script: True (available)
    else Port In Use
        HTTP Client->>Port: Connection attempt
        Port-->>HTTP Client: HTTP 200 OK
        HTTP Client-->>check_port_available: Response
        check_port_available-->>Script: False (in use)
    end
```

## 📦 Subprocess Command Construction

```mermaid
graph LR
    A[Command Building] --> B[sys.executable]
    B --> C[-m]
    C --> D[mcp_server_opensearch]
    D --> E[--transport]
    E --> F[stream]
    F --> G[--port]
    G --> H[9900]
    
    H --> I{Config file?}
    I -->|Yes| J[--config]
    J --> K[config.yaml path]
    I -->|No| L[Final Command]
    K --> L
    
    L --> M[Execute with Popen]
    
    style A fill:#4CAF50,color:#fff
    style D fill:#2196F3,color:#fff
    style H fill:#FF9800,color:#fff
    style K fill:#9C27B0,color:#fff
    style M fill:#F44336,color:#fff
```

### Example Command
```bash
python -m mcp_server_opensearch --transport stream --port 9900 --config mcp_server_config.yaml
```

## 💊 Health Check Loop

```mermaid
flowchart LR
    Start([Server Started]) --> InitCounter[counter = 0]
    InitCounter --> Loop{counter < 30?}
    
    Loop -->|Yes| TryHealth[GET /health]
    TryHealth --> CheckResponse{Status 200?}
    
    CheckResponse -->|Yes| Success[✅ Server Ready]
    CheckResponse -->|No| Sleep[Sleep 1s]
    
    Sleep --> Increment[counter++]
    Increment --> PrintProgress[Print attempt X/30]
    PrintProgress --> Loop
    
    Loop -->|No| Failed[⚠️ Health check failed]
    
    Success --> Ready([Ready for connections])
    Failed --> Warning([Show logs warning])
    
    style Start fill:#4CAF50,color:#fff
    style TryHealth fill:#2196F3,color:#fff
    style Success fill:#4CAF50,color:#fff
    style Failed fill:#FF9800,color:#fff
```

## 🔄 Process Lifecycle States

```mermaid
stateDiagram-v2
    [*] --> Checking: Script starts
    Checking --> PromptUser: Port in use
    Checking --> Loading: Port available
    
    PromptUser --> Exit: User declines
    PromptUser --> Loading: User accepts
    
    Loading --> Building: Config loaded
    Building --> Starting: Command built
    Starting --> HealthChecking: Process spawned
    
    HealthChecking --> Running: Health OK
    HealthChecking --> Warning: Health failed (continue)
    HealthChecking --> Error: Process died
    
    Running --> Terminating: Ctrl+C
    Warning --> Terminating: Ctrl+C
    
    Terminating --> Stopped: Graceful shutdown
    Stopped --> [*]
    
    Error --> [*]: Exit with error
    Exit --> [*]: User cancelled
    
    note right of Running
        Server ready to
        accept connections
    end note
    
    note right of HealthChecking
        Max 30 attempts
        1 second intervals
    end note
```

## 🔐 Environment & Configuration

```mermaid
graph TB
    subgraph "Environment Variables"
        A[MCP_SERVER_PORT] -->|default: 9900| B[Port Selection]
        C[OPENSEARCH_URL] --> D[Passed to subprocess]
        E[OPENSEARCH_USERNAME] --> D
        F[OPENSEARCH_PASSWORD] --> D
    end
    
    subgraph "Configuration File"
        G[mcp_server_config.yaml] -->|if exists| H[--config flag]
        H --> I[Server configuration]
        I --> J[OpenSearch connection]
        I --> K[Tool settings]
        I --> L[Logging options]
    end
    
    subgraph "python-dotenv"
        M[.env file] -->|load_dotenv| N[Environment variables]
        N --> O[Available to subprocess]
    end
    
    style B fill:#4CAF50,color:#fff
    style G fill:#2196F3,color:#fff
    style M fill:#FF9800,color:#fff
    style I fill:#9C27B0,color:#fff
```

## 🛡️ Error Handling

```mermaid
flowchart TD
    A[Script Execution] --> B{Try Block}
    
    B -->|FileNotFoundError| C[Package not installed]
    C --> D[Print install instructions]
    D --> E[Exit code 1]
    
    B -->|Exception| F[General error]
    F --> G[Print error message]
    G --> E
    
    B -->|KeyboardInterrupt| H[Ctrl+C pressed]
    H --> I[Terminate process]
    I --> J[Wait for exit]
    J --> K[Exit code 0]
    
    B -->|Success| L[Normal operation]
    L --> M[Wait for interrupt]
    M --> H
    
    style C fill:#F44336,color:#fff
    style F fill:#FF5722,color:#fff
    style H fill:#FF9800,color:#fff
    style K fill:#4CAF50,color:#fff
```

## 📊 Output Messages

### Startup Messages
```mermaid
graph LR
    A[🚀 Starting MCP Server...] --> B[📍 Port: 9900]
    B --> C[🔗 Endpoint: http://localhost:9900/sse]
    C --> D[📄 Using config file]
    D --> E[✅ MCP Server started PID]
    E --> F[Waiting for server...]
    
    style A fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
```

### Ready Messages
```mermaid
graph TD
    A[✅ MCP Server is ready!] --> B[You can now start the Gradio app]
    B --> C[python app.py]
    C --> D[Press Ctrl+C to stop]
    
    style A fill:#4CAF50,color:#fff
    style C fill:#2196F3,color:#fff
```

### Error Messages
```mermaid
graph TD
    A[⚠️ Port already in use] --> B[Do you want to continue?]
    C[❌ Package not found!] --> D[pip install opensearch-mcp-server-py]
    E[⚠️ Health check failed] --> F[Check server logs]
    
    style A fill:#FF9800,color:#fff
    style C fill:#F44336,color:#fff
    style E fill:#FF9800,color:#fff
```

## 🎯 Key Features

### 1. **Port Conflict Detection**
- Checks if port is already in use
- Prompts user before proceeding
- Prevents accidental multiple instances

### 2. **Automatic Configuration Loading**
- Detects `mcp_server_config.yaml`
- Loads `.env` file if available
- Passes environment to subprocess

### 3. **Health Monitoring**
- Polls `/health` endpoint
- Retries up to 30 times
- 1-second intervals
- Clear progress indication

### 4. **Graceful Shutdown**
- Catches Ctrl+C signal
- Terminates subprocess cleanly
- Waits for process exit
- Prints confirmation message

## 🔧 Process Management

```mermaid
sequenceDiagram
    participant User
    participant Script
    participant Subprocess
    participant MCP Server
    participant OpenSearch
    
    User->>Script: python start_mcp_server.py
    Script->>Script: Check port availability
    Script->>Subprocess: Popen(command)
    Subprocess->>MCP Server: Start process
    
    loop Health Check (max 30)
        Script->>MCP Server: GET /health
        alt Server Ready
            MCP Server-->>Script: 200 OK
        else Not Ready
            MCP Server-->>Script: No response
            Script->>Script: Sleep 1s
        end
    end
    
    MCP Server->>OpenSearch: Test connection
    OpenSearch-->>MCP Server: Connection OK
    
    Script-->>User: ✅ Server ready
    
    Note over Script,MCP Server: Server running...
    
    User->>Script: Ctrl+C
    Script->>Subprocess: terminate()
    Subprocess->>MCP Server: SIGTERM
    MCP Server->>MCP Server: Cleanup
    MCP Server-->>Subprocess: Exit
    Subprocess-->>Script: Process ended
    Script-->>User: ✅ Server stopped
```

## 🧪 Usage Examples

### Basic Usage
```bash
python start_mcp_server.py
```

### Custom Port
```bash
MCP_SERVER_PORT=9999 python start_mcp_server.py
```

### With Configuration
```bash
# Assumes mcp_server_config.yaml exists
python start_mcp_server.py
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```
   ⚠️ Port 9900 is already in use
   ```
   - **Solution**: Stop existing MCP server or choose different port

2. **Package Not Found**
   ```
   ❌ MCP server package not found!
   ```
   - **Solution**: `pip install opensearch-mcp-server-py`

3. **Health Check Timeout**
   ```
   ⚠️ Server started but health check failed
   ```
   - **Solution**: Check OpenSearch connection, review logs

4. **Permission Denied**
   ```
   Error: Permission denied on port 9900
   ```
   - **Solution**: Use port > 1024 or run with appropriate permissions

## 📈 Performance Considerations

### Subprocess vs Threading
```mermaid
graph TB
    A[Why subprocess.Popen?] --> B[Separate process]
    B --> C[Independent lifecycle]
    C --> D[Better isolation]
    D --> E[Easier monitoring]
    
    F[vs Threading] --> G[Shared memory]
    G --> H[GIL limitations]
    H --> I[Harder to control]
    
    style B fill:#4CAF50,color:#fff
    style G fill:#FF9800,color:#fff
```

### Health Check Timing
- **30 attempts** × **1 second** = **30 seconds max wait**
- Balances responsiveness vs reliability
- Prevents indefinite hanging
- User can see progress

## 🔄 Integration with App

```mermaid
graph LR
    A[Terminal 1] -->|Run| B[start_mcp_server.py]
    B --> C[MCP Server Running]
    C -->|Port 9900| D[SSE Endpoint]
    
    E[Terminal 2] -->|Run| F[app.py]
    F --> G[MCPClient]
    G -->|Connect to| D
    
    D <-->|Tool Calls| H[OpenSearch]
    
    style B fill:#4CAF50,color:#fff
    style C fill:#2196F3,color:#fff
    style F fill:#FF9800,color:#fff
    style H fill:#9C27B0,color:#fff
```

## 📚 Related Files

- `mcp_client.py` - Client that connects to this server
- `app.py` - Gradio application using the MCP server
- `mcp_server_config.yaml` - Server configuration
- `.env` - Environment variables

## 🔗 External Dependencies

- `mcp_server_opensearch` - The actual MCP server package
- `requests` - For health check HTTP calls
- `python-dotenv` - Optional, for loading `.env` files
- `subprocess` - Built-in, for process management

---

**Version**: 1.0  
**Last Updated**: 2025-11-30  
**Maintainer**: OpenSearch MCP Demo Team
