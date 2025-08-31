#!/usr/bin/env node

// Simple test script for the OKR MCP server
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function testMCPServer() {
  console.log('🧪 Testing OKR MCP Server...\n');

  // Start the MCP server
  const serverPath = join(__dirname, 'dist', 'index.js');
  const server = spawn('node', [serverPath], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  // Test requests
  const testRequests = [
    {
      name: 'List Tools',
      request: {
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/list',
        params: {}
      }
    },
    {
      name: 'Ask OKR - Basic Query',
      request: {
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: {
          name: 'ask_okr',
          arguments: {
            query: 'what are the objectives'
          }
        }
      }
    },
    {
      name: 'List Teams',
      request: {
        jsonrpc: '2.0',
        id: 3,
        method: 'tools/call',
        params: {
          name: 'list_teams',
          arguments: {}
        }
      }
    }
  ];

  let testIndex = 0;
  
  function runNextTest() {
    if (testIndex >= testRequests.length) {
      console.log('✅ All tests completed!');
      server.kill();
      return;
    }

    const test = testRequests[testIndex++];
    console.log(`🔍 Testing: ${test.name}`);
    
    const requestStr = JSON.stringify(test.request) + '\n';
    server.stdin.write(requestStr);
  }

  // Handle server output
  let buffer = '';
  server.stdout.on('data', (data) => {
    buffer += data.toString();
    
    // Try to parse complete JSON responses
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer
    
    lines.forEach(line => {
      if (line.trim()) {
        try {
          const response = JSON.parse(line);
          console.log('📝 Response:', JSON.stringify(response, null, 2));
          console.log('---\n');
          
          // Run next test after a short delay
          setTimeout(runNextTest, 100);
        } catch (e) {
          console.log('📄 Raw output:', line);
        }
      }
    });
  });

  server.stderr.on('data', (data) => {
    console.log('ℹ️  Server info:', data.toString());
  });

  server.on('close', (code) => {
    console.log(`🏁 Server exited with code ${code}`);
  });

  // Start first test
  setTimeout(runNextTest, 1000);

  // Clean exit after timeout
  setTimeout(() => {
    console.log('⏰ Test timeout, killing server');
    server.kill();
    process.exit(0);
  }, 10000);
}

testMCPServer().catch(console.error);
