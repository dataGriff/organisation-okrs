# OKR Agent MCP Server

This is a Model Context Protocol (MCP) server that exposes your OKR Agent as tools that can be used by AI assistants like Claude Desktop, Cline, or any other MCP-compatible client.

## Features

The MCP server provides these tools:

- **`ask_okr`** - Ask natural language questions about OKRs
- **`search_okr`** - Perform semantic search across OKR content  
- **`list_teams`** - Get available teams
- **`list_quarters`** - Get available quarters
- **`download_okr_files`** - Get information about downloadable OKR files
- **`refresh_okr_data`** - Refresh the OKR data cache

## Installation

```bash
cd mcp-server
npm install
npm run build
```

## Configuration

### Environment Variables

- `OKR_API_URL` - URL of your OKR Agent API (default: `http://localhost:8000`)

### Claude Desktop Configuration

Add this to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "okr-agent": {
      "command": "node",
      "args": ["/path/to/organisation-okrs/mcp-server/dist/index.js"],
      "env": {
        "OKR_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### VS Code with Cline

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "okr-agent": {
      "command": "node",
      "args": ["/path/to/organisation-okrs/mcp-server/dist/index.js"],
      "env": {
        "OKR_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Usage Examples

Once configured, you can use natural language with your AI assistant:

### Basic Queries
- "What are the current objectives?"
- "Show me the key results for the Platform team"
- "What are the risks for Sales in Q3?"

### Filtered Queries  
- "What are Platform's objectives for 2025-Q3?"
- "Show me all key results for Sales team"
- "Search for performance improvements in Platform team"

### Team and Quarter Management
- "List all teams"
- "What quarters are available?"
- "Show me teams that have OKRs in 2025-Q3"

### Data Management
- "Refresh the OKR data"
- "What files would be included if I download Platform's OKRs?"

## Development

### Running in Development
```bash
npm run dev
```

### Building
```bash
npm run build
```

### Testing the Server
You can test the MCP server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

## Tool Reference

### ask_okr
Ask natural language questions about OKRs with optional filtering.

**Parameters:**
- `query` (required): The question about OKRs
- `team` (optional): Filter by team name
- `quarter` (optional): Filter by quarter (e.g., "2025-Q3")
- `k` (optional): Maximum results (default: 50)

**Example:**
```json
{
  "query": "what are the objectives",
  "team": "Platform",
  "quarter": "2025-Q3"
}
```

### search_okr
Perform semantic search across OKR content.

**Parameters:**
- `query` (required): Search query
- `team` (optional): Filter by team
- `quarter` (optional): Filter by quarter  
- `k` (optional): Number of results (default: 10)

### list_teams
Get all available teams.

**Parameters:**
- `quarter` (optional): Filter teams by quarter

### list_quarters  
Get all available quarters.

**Parameters:**
- `team` (optional): Filter quarters by team

### download_okr_files
Get information about downloadable OKR files.

**Parameters:**
- `query` (required): Query to filter files
- `team` (optional): Filter by team
- `quarter` (optional): Filter by quarter
- `format` (optional): Download format ("zip")
- `k` (optional): Max files (default: 50)

### refresh_okr_data
Refresh the OKR data cache.

**Parameters:** None

## Integration Benefits

Using MCP for your OKR agent provides several advantages:

### 1. **Native AI Assistant Integration**
- Works seamlessly with Claude Desktop, Cline, and other MCP clients
- No need for custom interfaces or commands
- Natural language interaction

### 2. **Standardized Protocol**
- Uses the industry-standard Model Context Protocol
- Automatic tool discovery and documentation
- Type-safe parameter validation

### 3. **Rich Context Awareness**
- AI assistants can use OKR tools as part of larger workflows
- Combine OKR queries with other tools and reasoning
- Maintain context across multiple queries

### 4. **Better User Experience**
- No need to remember API endpoints or parameters
- Natural language queries instead of structured API calls
- Rich formatted responses with emojis and structure

### 5. **Composability**
- Combine with other MCP servers (databases, file systems, etc.)
- Build complex workflows involving OKRs and other systems
- Chain multiple OKR queries together

## Example Workflows

With MCP, users can have natural conversations like:

> **User:** "What are Platform's current objectives?"
> 
> **Assistant:** *[Uses ask_okr tool]* Platform has two main objectives:
> 🎯 Reduce lead time
> 🎯 Improve reliability and performance of core APIs
>
> **User:** "What are the key results for the second objective?"
>
> **Assistant:** *[Uses ask_okr with filtered query]* For improving reliability and performance:
> 📈 KR1: Reduce p95 latency from 420ms → 250ms
> 📈 KR2: Cut weekly incident count from 7 → 2
> 📈 KR3: ≥ 95% SLO compliance for 12 consecutive weeks
> 📈 KR4: Migrate 80% of services to v2 observability stack

This creates a much more natural and powerful experience than traditional API calls or Slack bots!
