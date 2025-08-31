#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import { z } from 'zod';

// Configuration
const OKR_API_BASE = process.env.OKR_API_URL || 'http://localhost:8000';

// Validation schemas
const AskToolArgsSchema = z.object({
  query: z.string().describe('The question or search query about OKRs'),
  team: z.string().optional().describe('Filter by specific team (e.g., "Platform", "Sales")'),
  quarter: z.string().optional().describe('Filter by specific quarter (e.g., "2025-Q3")'),
  k: z.number().optional().default(50).describe('Maximum number of results to return'),
});

const SearchToolArgsSchema = z.object({
  query: z.string().describe('Semantic search query for OKR content'),
  team: z.string().optional().describe('Filter by specific team'),
  quarter: z.string().optional().describe('Filter by specific quarter'),
  k: z.number().optional().default(10).describe('Number of search results to return'),
});

const TeamsToolArgsSchema = z.object({
  quarter: z.string().optional().describe('Filter teams by quarter'),
});

const QuartersToolArgsSchema = z.object({
  team: z.string().optional().describe('Filter quarters by team'),
});

const DownloadToolArgsSchema = z.object({
  query: z.string().describe('Query to filter which OKR files to download'),
  team: z.string().optional().describe('Filter by specific team'),
  quarter: z.string().optional().describe('Filter by specific quarter'),
  format: z.enum(['zip']).default('zip').describe('Download format'),
  k: z.number().optional().default(50).describe('Maximum number of files to include'),
});

// API client functions
async function queryOKRAgent(endpoint: string, params: Record<string, any>) {
  try {
    const response = await axios.get(`${OKR_API_BASE}${endpoint}`, {
      params,
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`OKR API error: ${error.message}`);
    }
    throw error;
  }
}

// Create server instance
const server = new Server({
  name: 'okr-agent-mcp',
  version: '1.0.0',
  capabilities: {
    tools: {},
  },
});

// Tool definitions
const tools: Tool[] = [
  {
    name: 'ask_okr',
    description: 'Ask natural language questions about OKRs (Objectives and Key Results). Supports filtering by team and quarter.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The question or search query about OKRs (e.g., "what are the objectives", "key results for platform team")',
        },
        team: {
          type: 'string',
          description: 'Optional: Filter by specific team (e.g., "Platform", "Sales")',
        },
        quarter: {
          type: 'string',
          description: 'Optional: Filter by specific quarter (e.g., "2025-Q3")',
        },
        k: {
          type: 'number',
          description: 'Optional: Maximum number of results to return (default: 50)',
          default: 50,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'search_okr',
    description: 'Perform semantic search across OKR content to find relevant information.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Semantic search query for OKR content',
        },
        team: {
          type: 'string',
          description: 'Optional: Filter by specific team',
        },
        quarter: {
          type: 'string',
          description: 'Optional: Filter by specific quarter',
        },
        k: {
          type: 'number',
          description: 'Optional: Number of search results to return (default: 10)',
          default: 10,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'list_teams',
    description: 'Get a list of all teams that have OKRs.',
    inputSchema: {
      type: 'object',
      properties: {
        quarter: {
          type: 'string',
          description: 'Optional: Filter teams by quarter',
        },
      },
      required: [],
    },
  },
  {
    name: 'list_quarters',
    description: 'Get a list of all quarters that have OKRs.',
    inputSchema: {
      type: 'object',
      properties: {
        team: {
          type: 'string',
          description: 'Optional: Filter quarters by team',
        },
      },
      required: [],
    },
  },
  {
    name: 'download_okr_files',
    description: 'Download OKR files that match a query as a ZIP archive.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Query to filter which OKR files to download',
        },
        team: {
          type: 'string',
          description: 'Optional: Filter by specific team',
        },
        quarter: {
          type: 'string',
          description: 'Optional: Filter by specific quarter',
        },
        format: {
          type: 'string',
          enum: ['zip'],
          description: 'Download format (currently only "zip" is supported)',
          default: 'zip',
        },
        k: {
          type: 'number',
          description: 'Optional: Maximum number of files to include (default: 50)',
          default: 50,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'refresh_okr_data',
    description: 'Refresh the OKR data cache to pick up any new or updated OKR files.',
    inputSchema: {
      type: 'object',
      properties: {},
      required: [],
    },
  },
];

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'ask_okr': {
        const { query, team, quarter, k } = AskToolArgsSchema.parse(args);
        const params: Record<string, any> = { q: query, k };
        if (team) params.team = team;
        if (quarter) params.quarter = quarter;

        const result = await queryOKRAgent('/ask', params);
        
        // Format response for better readability
        let formattedResponse = `**Query:** ${query}\n`;
        if (team) formattedResponse += `**Team:** ${team}\n`;
        if (quarter) formattedResponse += `**Quarter:** ${quarter}\n`;
        formattedResponse += '\n**Results:**\n';
        
        if (result.bullets && result.bullets.length > 0) {
          result.bullets.forEach((bullet: string, index: number) => {
            if (bullet.startsWith('Objective:')) {
              formattedResponse += `\n🎯 **${bullet}**\n`;
            } else if (bullet.startsWith('KR')) {
              formattedResponse += `  📈 ${bullet}\n`;
            } else if (bullet.toLowerCase().includes('risk')) {
              formattedResponse += `  ⚠️ ${bullet}\n`;
            } else {
              formattedResponse += `  • ${bullet}\n`;
            }
          });
        } else {
          formattedResponse += 'No results found.';
        }

        return {
          content: [
            {
              type: 'text',
              text: formattedResponse,
            },
          ],
        };
      }

      case 'search_okr': {
        const { query, team, quarter, k } = SearchToolArgsSchema.parse(args);
        const params: Record<string, any> = { q: query, k };
        if (team) params.team = team;
        if (quarter) params.quarter = quarter;

        const result = await queryOKRAgent('/search', params);
        
        let formattedResponse = `**Semantic Search:** ${query}\n`;
        if (team) formattedResponse += `**Team:** ${team}\n`;
        if (quarter) formattedResponse += `**Quarter:** ${quarter}\n`;
        formattedResponse += '\n**Search Results:**\n';
        
        if (result.results && result.results.length > 0) {
          result.results.forEach((item: any, index: number) => {
            formattedResponse += `\n**${index + 1}.** ${item.content}\n`;
            if (item.metadata) {
              formattedResponse += `   *Source: ${item.metadata.path || 'Unknown'}*\n`;
              if (item.metadata.team) formattedResponse += `   *Team: ${item.metadata.team}*\n`;
              if (item.metadata.quarter) formattedResponse += `   *Quarter: ${item.metadata.quarter}*\n`;
            }
          });
        } else {
          formattedResponse += 'No search results found.';
        }

        return {
          content: [
            {
              type: 'text',
              text: formattedResponse,
            },
          ],
        };
      }

      case 'list_teams': {
        const { quarter } = TeamsToolArgsSchema.parse(args);
        
        // Use the ask endpoint to get team information
        const params: Record<string, any> = { q: 'teams', k: 100 };
        if (quarter) params.quarter = quarter;
        
        const result = await queryOKRAgent('/ask', params);
        
        // Extract teams from citations
        const teams = new Set<string>();
        if (result.citations) {
          result.citations.forEach((citation: any) => {
            if (citation.path && citation.path.includes('teams/')) {
              const teamName = citation.path.split('teams/')[1]?.split('/')[0];
              if (teamName) {
                teams.add(teamName.charAt(0).toUpperCase() + teamName.slice(1));
              }
            }
          });
        }

        let formattedResponse = '**Available Teams:**\n';
        if (quarter) formattedResponse += `*Filtered by quarter: ${quarter}*\n\n`;
        
        if (teams.size > 0) {
          Array.from(teams).sort().forEach((team) => {
            formattedResponse += `• ${team}\n`;
          });
        } else {
          formattedResponse += 'No teams found.';
        }

        return {
          content: [
            {
              type: 'text',
              text: formattedResponse,
            },
          ],
        };
      }

      case 'list_quarters': {
        const { team } = QuartersToolArgsSchema.parse(args);
        
        // Use the ask endpoint to get quarter information
        const params: Record<string, any> = { q: 'quarters', k: 100 };
        if (team) params.team = team;
        
        const result = await queryOKRAgent('/ask', params);
        
        // Extract quarters from citations
        const quarters = new Set<string>();
        if (result.citations) {
          result.citations.forEach((citation: any) => {
            if (citation.path) {
              // Try to extract quarter from filename or metadata
              const quarterMatch = citation.path.match(/(\d{4}-Q[1-4])/);
              if (quarterMatch) {
                quarters.add(quarterMatch[1]);
              }
            }
          });
        }

        let formattedResponse = '**Available Quarters:**\n';
        if (team) formattedResponse += `*Filtered by team: ${team}*\n\n`;
        
        if (quarters.size > 0) {
          Array.from(quarters).sort().forEach((quarter) => {
            formattedResponse += `• ${quarter}\n`;
          });
        } else {
          formattedResponse += 'No quarters found.';
        }

        return {
          content: [
            {
              type: 'text',
              text: formattedResponse,
            },
          ],
        };
      }

      case 'download_okr_files': {
        const { query, team, quarter, format, k } = DownloadToolArgsSchema.parse(args);
        const params: Record<string, any> = { q: query, format, k };
        if (team) params.team = team;
        if (quarter) params.quarter = quarter;

        // Note: This would typically return binary data
        // For MCP, we'll return information about what would be downloaded
        const result = await queryOKRAgent('/ask', params);
        
        let formattedResponse = `**Download Request:**\n`;
        formattedResponse += `Query: ${query}\n`;
        if (team) formattedResponse += `Team: ${team}\n`;
        if (quarter) formattedResponse += `Quarter: ${quarter}\n`;
        formattedResponse += `Format: ${format}\n\n`;
        
        if (result.citations && result.citations.length > 0) {
          formattedResponse += `**Files that would be included (${result.citations.length}):**\n`;
          result.citations.forEach((citation: any, index: number) => {
            formattedResponse += `${index + 1}. ${citation.path}\n`;
          });
          formattedResponse += `\n*Use the download endpoint directly at: ${OKR_API_BASE}/download?${new URLSearchParams(params).toString()}*`;
        } else {
          formattedResponse += 'No files match the query.';
        }

        return {
          content: [
            {
              type: 'text',
              text: formattedResponse,
            },
          ],
        };
      }

      case 'refresh_okr_data': {
        const result = await queryOKRAgent('/refresh', {});
        
        return {
          content: [
            {
              type: 'text',
              text: `**OKR Data Refresh:** ${result.status || 'completed'}\n${result.message || 'Data cache has been refreshed successfully.'}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('OKR Agent MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
