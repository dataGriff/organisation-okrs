# GitHub Copilot + MCP Integration Guide

This guide shows how to use your OKR Agent with GitHub Copilot through the MCP (Model Context Protocol) extension.

## Setup Instructions

### 1. Install Required Extensions

Install the Copilot MCP extension:
- Extension ID: `automatalabs.copilot-mcp`
- Or search for "Copilot MCP" in the VS Code extension marketplace

### 2. Build the MCP Server

```bash
cd mcp-server
npm install
npm run build
```

### 3. Configure Copilot MCP Extension

1. **Open VS Code Settings** (Ctrl/Cmd + ,)
2. **Search for "Copilot MCP"**
3. **Set the MCP Configuration File** to point to:
   ```
   /workspaces/organisation-okrs/mcp-server/copilot-mcp-config.json
   ```

Or manually configure in your VS Code settings.json:

```json
{
  "copilot-mcp.configPath": "/workspaces/organisation-okrs/mcp-server/copilot-mcp-config.json",
  "copilot-mcp.autoStart": true,
  "copilot-mcp.logLevel": "info"
}
```

### 4. Start Your OKR Agent

Ensure your OKR Agent API is running:

```bash
cd ../okr-agent
docker-compose up -d
```

Verify it's working:
```bash
curl "http://localhost:8000/ask?q=test"
```

### 5. Restart VS Code

Restart VS Code to ensure all extensions and configurations are loaded.

## Usage with GitHub Copilot Chat

Once configured, you can use your OKR agent through GitHub Copilot Chat:

### Basic OKR Queries

Open Copilot Chat (Ctrl/Cmd + Shift + I) and try these examples:

**Query Objectives:**
```
@copilot What are the current objectives for Platform team?
```

**Query Key Results:**
```
@copilot Show me the key results for Sales team in 2025-Q3
```

**Search OKRs:**
```
@copilot Search for anything related to "performance improvements" in our OKRs
```

**List Teams:**
```
@copilot What teams have OKRs?
```

**Get All OKRs:**
```
@copilot Show me all objectives and key results
```

### Advanced Queries

**Filtered Queries:**
```
@copilot What are Platform's objectives for reducing lead time?
```

**Risk Analysis:**
```
@copilot What risks are associated with Sales team's OKRs?
```

**Cross-team Analysis:**
```
@copilot Compare the objectives between Platform and Sales teams
```

## Integration with Coding Workflows

### Context-Aware Development

**Relate Code to OKRs:**
```
@copilot I'm working on API performance improvements. What OKRs relate to this? Then help me write optimized code.
```

**Feature Planning:**
```
@copilot What are Platform's key results for API reliability? Help me create a monitoring system for these metrics.
```

**Documentation:**
```
@copilot Generate documentation for this function and link it to relevant OKRs about performance improvements.
```

### Example Workflow

1. **Query OKRs:**
   ```
   @copilot What are Platform's current objectives?
   ```

2. **Get Implementation Guidance:**
   ```
   @copilot Based on the "reduce lead time" objective, help me optimize this deployment script
   ```

3. **Create Monitoring:**
   ```
   @copilot Create a dashboard component to track the latency KR we just discussed
   ```

4. **Document Progress:**
   ```
   @copilot Write a progress update for the API performance KRs
   ```

## Available MCP Tools

Your OKR Agent provides these tools to Copilot:

### `ask_okr`
- **Purpose:** Ask natural language questions about OKRs
- **Usage:** `@copilot Ask about sales objectives using ask_okr`
- **Parameters:** query, team (optional), quarter (optional), k (optional)

### `search_okr`
- **Purpose:** Semantic search across OKR content
- **Usage:** `@copilot Search for "reliability" in OKRs using search_okr`
- **Parameters:** query, team (optional), quarter (optional), k (optional)

### `list_teams`
- **Purpose:** Get all available teams
- **Usage:** `@copilot List all teams using list_teams`
- **Parameters:** quarter (optional)

### `list_quarters`
- **Purpose:** Get all available quarters
- **Usage:** `@copilot Show available quarters using list_quarters`
- **Parameters:** team (optional)

### `download_okr_files`
- **Purpose:** Get information about downloadable OKR files
- **Usage:** `@copilot What files can I download for Platform team?`
- **Parameters:** query, team (optional), quarter (optional), format, k (optional)

### `refresh_okr_data`
- **Purpose:** Refresh the OKR data cache
- **Usage:** `@copilot Refresh the OKR data using refresh_okr_data`
- **Parameters:** None

## Troubleshooting

### Copilot Can't Find MCP Tools

1. **Check Extension Installation:**
   - Ensure `automatalabs.copilot-mcp` is installed and enabled
   - Restart VS Code

2. **Verify Configuration:**
   - Check that `copilot-mcp-config.json` path is correct in settings
   - Ensure the JSON syntax is valid

3. **Check MCP Server:**
   - Verify the MCP server built successfully: `ls dist/index.js`
   - Test manually: `node dist/index.js`

### OKR Agent Not Responding

1. **Check API Status:**
   ```bash
   curl "http://localhost:8000/ask?q=test"
   ```

2. **Check Docker Status:**
   ```bash
   docker-compose ps
   ```

3. **Check Logs:**
   ```bash
   docker-compose logs okr-agent
   ```

### MCP Server Connection Issues

1. **Check Node.js Version:**
   ```bash
   node --version  # Should be >= 18
   ```

2. **Rebuild MCP Server:**
   ```bash
   npm run build
   ```

3. **Check Environment Variables:**
   - Ensure `OKR_API_URL` is set correctly
   - Verify the OKR agent is accessible from the URL

### Copilot Chat Not Using Tools

1. **Be Explicit:** Mention that you want to use OKR tools:
   ```
   @copilot Use the OKR agent to find Platform's objectives
   ```

2. **Check Tool Names:** Reference specific tools:
   ```
   @copilot Use ask_okr to find sales key results
   ```

3. **Restart Extensions:**
   - Disable and re-enable the Copilot MCP extension
   - Restart VS Code

## Pro Tips

### 1. **Be Specific with Queries**
Instead of: `@copilot Show me objectives`
Try: `@copilot Use ask_okr to show Platform team's objectives for 2025-Q3`

### 2. **Combine with Coding Tasks**
```
@copilot First, get Platform's API performance KRs, then help me write monitoring code for them
```

### 3. **Use Contextual Follow-ups**
```
User: @copilot What are Platform's objectives?
Copilot: [Shows objectives]
User: Now help me write tests for the latency improvements mentioned in KR1
```

### 4. **Leverage Multiple Tools**
```
@copilot List all teams, then show me the objectives for each team
```

## Benefits of Copilot + MCP + OKR Integration

### 🎯 **Contextual Coding**
- Write code that directly supports your OKRs
- Understand business impact of technical decisions
- Align development work with company goals

### 📊 **Data-Driven Development**
- Reference specific metrics from key results
- Build monitoring for OKR targets
- Create dashboards for business objectives

### 🔄 **Streamlined Workflow**
- No context switching between tools
- Direct access to OKR data while coding
- Natural language queries in familiar interface

### 💡 **Enhanced Decision Making**
- Prioritize features based on OKRs
- Understand which code changes matter most
- Connect technical debt to business objectives
