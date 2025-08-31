# VS Code MCP Integration Guide

This guide shows how to use your OKR Agent with VS Code through MCP-compatible extensions.

## Option 1: Cline Extension (Recommended)

Cline is the most popular AI coding assistant for VS Code that supports MCP.

### Setup Steps:

1. **Install the MCP Server:**
   ```bash
   cd mcp-server
   ./setup.sh
   ```

2. **Install Cline Extension:**
   - Install the "Cline" extension (`saoudrizwan.claude-dev`)
   - Or install from the extension list above

3. **Configure MCP in Cline:**
   - Open VS Code settings (Cmd/Ctrl + ,)
   - Search for "Cline MCP"
   - Set the MCP servers configuration to point to `cline-mcp-config.json`:
   
   ```json
   {
     "mcpServers": {
       "okr-agent": {
         "command": "node",
         "args": ["/workspaces/organisation-okrs/mcp-server/dist/index.js"],
         "env": {
           "OKR_API_URL": "http://localhost:8000"
         }
       }
     }
   }
   ```

4. **Start Your OKR Agent:**
   ```bash
   cd ../okr-agent
   docker-compose up -d
   ```

5. **Use with Cline:**
   - Open Cline chat panel in VS Code
   - Ask questions like:
     - "What are the current objectives?"
     - "Show me Platform's key results"
     - "List all teams with OKRs"

## Option 2: Continue Extension

Continue is another popular AI extension that supports MCP.

### Setup Steps:

1. Install Continue extension (`continue.continue`)
2. Configure MCP servers in Continue settings
3. Use the same MCP configuration as above

## Option 3: Copilot MCP Extension

For GitHub Copilot users, there's a dedicated MCP extension.

### Setup Steps:

1. Install Copilot MCP extension (`automatalabs.copilot-mcp`)
2. Configure OKR agent as MCP server
3. Use through GitHub Copilot interface

## Example Usage with Cline

Once set up, you can have conversations like:

**You:** "What are Platform team's current objectives?"

**Cline:** *[Uses ask_okr tool automatically]*
Based on the OKR data, Platform team has two main objectives:

🎯 **Objective: Reduce lead time**
  📈 KR1: Lead time under 2 days.
  📈 KR2: Lead time under 1 day.

🎯 **Objective: Improve reliability and performance of core APIs**
  📈 KR1: Reduce p95 latency from 420ms → 250ms.
  📈 KR2: Cut weekly incident count from 7 → 2.
  📈 KR3: ≥ 95% SLO compliance for 12 consecutive weeks.
  📈 KR4: Migrate 80% of services to v2 observability stack.

**You:** "Which objective seems more at risk?"

**Cline:** *[Uses search_okr to find risk information]*
Let me check the risk information... 

Based on the OKR data, the "Reduce lead time" objective mentions "Architectural difficulties" as a risk, which suggests this might be the more challenging objective.

## Benefits of VS Code + MCP Integration

### 🎯 **Context-Aware Assistance**
- Cline can query your OKRs while helping with code
- Relate code changes to business objectives
- Understand project priorities

### 💬 **Natural Language Interface**
- Ask questions in plain English
- No need to remember API endpoints
- AI handles the tool selection automatically

### 🔄 **Workflow Integration**
- Combine OKR queries with coding tasks
- Document code with relevant OKR context
- Plan features based on key results

### 📊 **Multi-Tool Workflows**
Example workflow:
1. "What are the Platform team's current objectives?"
2. "Help me write code to improve API latency" (relates to KR1)
3. "Create a monitoring dashboard for these metrics"
4. "Generate documentation linking this code to our OKRs"

## Troubleshooting

### MCP Server Not Starting
- Ensure Node.js is installed
- Check that the MCP server built successfully: `npm run build`
- Verify the path in your MCP configuration

### OKR Agent Not Responding
- Ensure your OKR agent is running: `docker-compose up -d`
- Check the API URL in your MCP configuration
- Test the API directly: `curl http://localhost:8000/ask?q=test`

### Extension Not Recognizing MCP
- Restart VS Code after configuration changes
- Check extension logs for errors
- Verify MCP configuration syntax

## Advanced Configuration

### Custom Environment Variables
```json
{
  "mcpServers": {
    "okr-agent": {
      "command": "node",
      "args": ["/workspaces/organisation-okrs/mcp-server/dist/index.js"],
      "env": {
        "OKR_API_URL": "http://localhost:8000",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

### Multiple Environments
```json
{
  "mcpServers": {
    "okr-agent-dev": {
      "command": "node",
      "args": ["/workspaces/organisation-okrs/mcp-server/dist/index.js"],
      "env": {
        "OKR_API_URL": "http://localhost:8000"
      }
    },
    "okr-agent-prod": {
      "command": "node", 
      "args": ["/workspaces/organisation-okrs/mcp-server/dist/index.js"],
      "env": {
        "OKR_API_URL": "https://okr-api.yourcompany.com"
      }
    }
  }
}
```
