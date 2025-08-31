#!/bin/bash

# Build and setup script for OKR Agent MCP Server

echo "🔧 Setting up OKR Agent MCP Server..."

cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the TypeScript
echo "🏗️  Building TypeScript..."
npm run build

# Check if build was successful
if [ ! -f "dist/index.js" ]; then
    echo "❌ Build failed - dist/index.js not found"
    exit 1
fi

echo "✅ MCP Server built successfully!"

# Show configuration instructions
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Make sure your OKR Agent is running:"
echo "   cd ../okr-agent && docker-compose up -d"
echo ""
echo "2. Test the MCP server:"
echo "   npx @modelcontextprotocol/inspector node dist/index.js"
echo ""
echo "3. Add to Claude Desktop config:"
echo "   File: ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)"
echo "   File: %APPDATA%\\Claude\\claude_desktop_config.json (Windows)"
echo ""
echo "   Add this configuration:"
echo '   {'
echo '     "mcpServers": {'
echo '       "okr-agent": {'
echo '         "command": "node",'
echo "         \"args\": [\"$(pwd)/dist/index.js\"],"
echo '         "env": {'
echo '           "OKR_API_URL": "http://localhost:8000"'
echo '         }'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "4. Restart Claude Desktop to load the MCP server"
echo ""
echo "🚀 You can then ask Claude questions like:"
echo "   - What are the current objectives?"
echo "   - Show me Platform's key results"
echo "   - List all teams"
echo ""
echo "🎯 For VS Code Integration:"
echo "   1. Install Cline extension: saoudrizwan.claude-dev"
echo "   2. Configure MCP servers using cline-mcp-config.json"
echo "   3. See VS-CODE-SETUP.md for detailed instructions"
echo ""
