#!/bin/bash

# Test script to verify OKR Agent + MCP integration for VS Code

echo "🧪 Testing OKR Agent + MCP Integration..."

# Check if OKR Agent is running
echo "🔍 Checking OKR Agent status..."
if curl -s "http://localhost:8000/ask?q=test" > /dev/null 2>&1; then
    echo "✅ OKR Agent is running"
else
    echo "🚀 Starting OKR Agent..."
    cd okr-agent
    docker-compose up -d
    cd ..
    echo "⏳ Waiting for OKR Agent to start..."
    sleep 5
    
    if curl -s "http://localhost:8000/ask?q=test" > /dev/null 2>&1; then
        echo "✅ OKR Agent started successfully"
    else
        echo "❌ Failed to start OKR Agent"
        exit 1
    fi
fi

# Test OKR Agent API
echo "🔍 Testing OKR Agent API..."
RESPONSE=$(curl -s "http://localhost:8000/ask?q=what%20are%20the%20objectives&team=Platform")
if echo "$RESPONSE" | jq -e '.bullets[]' > /dev/null 2>&1; then
    echo "✅ OKR Agent API is working"
    echo "📊 Sample response:"
    echo "$RESPONSE" | jq -r '.bullets[0:2][]' | head -2
else
    echo "❌ OKR Agent API test failed"
    exit 1
fi

# Check MCP server build
echo "🔍 Checking MCP server..."
if [ -f "mcp-server/dist/index.js" ]; then
    echo "✅ MCP server is built"
else
    echo "🏗️ Building MCP server..."
    cd mcp-server
    npm run build
    cd ..
    
    if [ -f "mcp-server/dist/index.js" ]; then
        echo "✅ MCP server built successfully"
    else
        echo "❌ Failed to build MCP server"
        exit 1
    fi
fi

# Test MCP server (briefly)
echo "🔍 Testing MCP server..."
cd mcp-server
# Test that the MCP server can start and output its startup message
OUTPUT=$(timeout 3 node dist/index.js 2>&1)
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 124 ]] && [[ "$OUTPUT" == *"OKR Agent MCP server running on stdio"* ]]; then
    echo "✅ MCP server starts successfully"
elif [[ "$OUTPUT" == *"OKR Agent MCP server running on stdio"* ]]; then
    echo "✅ MCP server starts successfully"
else
    echo "❌ MCP server failed to start"
    echo "Error output: $OUTPUT"
    exit 1
fi
cd ..

# Check VS Code MCP configuration
echo "🔍 Checking VS Code MCP configuration..."
if [ -f ".vscode/mcp.json" ]; then
    echo "✅ VS Code MCP config exists"
    if jq -e '.servers["okr-agent"]' .vscode/mcp.json > /dev/null 2>&1; then
        echo "✅ OKR Agent is configured in MCP"
    else
        echo "❌ OKR Agent not found in MCP config"
        exit 1
    fi
else
    echo "❌ VS Code MCP config not found"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Your OKR Agent is ready for VS Code MCP integration."
echo ""
echo "📝 Next steps:"
echo "1. Install a VS Code extension that supports MCP:"
echo "   - GitHub Copilot (with MCP extension)"
echo "   - Cline (saoudrizwan.claude-dev)"
echo "   - Continue (continue.continue)"
echo ""
echo "2. Configure the extension to use MCP servers from .vscode/mcp.json"
echo ""
echo "3. Start asking questions like:"
echo "   - 'What are the current objectives?'"
echo "   - 'Show me Platform team's key results'"
echo "   - 'List all teams with OKRs'"
echo ""
