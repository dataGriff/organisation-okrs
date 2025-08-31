#!/bin/bash

# Quick setup script for GitHub Copilot + MCP integration

echo "🚀 Setting up OKR Agent for GitHub Copilot..."

# Navigate to MCP server directory
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the server
echo "🏗️ Building MCP server..."
npm run build

if [ ! -f "dist/index.js" ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ MCP Server built successfully!"

# Start OKR Agent if not running
echo "🔍 Checking if OKR Agent is running..."
if ! curl -s http://localhost:8000/ask?q=test > /dev/null 2>&1; then
    echo "🚀 Starting OKR Agent..."
    cd ../okr-agent
    docker-compose up -d
    echo "⏳ Waiting for OKR Agent to start..."
    sleep 5
    cd ../mcp-server
else
    echo "✅ OKR Agent is already running"
fi

# Test MCP server
echo "🧪 Testing MCP server..."
if node dist/index.js < /dev/null > /dev/null 2>&1 & then
    SERVER_PID=$!
    sleep 2
    kill $SERVER_PID 2>/dev/null
    echo "✅ MCP server test passed"
else
    echo "❌ MCP server test failed"
fi

echo ""
echo "🎯 Next Steps for GitHub Copilot Integration:"
echo ""
echo "1. Install the Copilot MCP extension:"
echo "   - Open VS Code Extensions (Ctrl+Shift+X)"
echo "   - Search for 'automatalabs.copilot-mcp'"
echo "   - Install the extension"
echo ""
echo "2. Configure the extension:"
echo "   - Open VS Code Settings (Ctrl+,)"
echo "   - Search for 'copilot-mcp'"
echo "   - Set config path to: $(pwd)/copilot-mcp-config.json"
echo ""
echo "3. Restart VS Code"
echo ""
echo "4. Test with Copilot Chat:"
echo "   - Open Copilot Chat (Ctrl+Shift+I)"
echo "   - Try: '@copilot What are the current objectives?'"
echo "   - Or: '@copilot Use ask_okr to show Platform team OKRs'"
echo ""
echo "📚 See COPILOT-SETUP.md for detailed instructions"
echo ""
