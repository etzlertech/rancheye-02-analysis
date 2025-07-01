#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

class SupabaseMCPServer {
  constructor() {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_ANON_KEY;
    
    if (!supabaseUrl || !supabaseKey) {
      throw new Error('SUPABASE_URL and SUPABASE_ANON_KEY must be set');
    }
    
    this.supabase = createClient(supabaseUrl, supabaseKey);
    this.server = new Server(
      {
        name: 'supabase-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );
    
    this.setupTools();
    this.setupErrorHandling();
  }
  
  setupTools() {
    // Query tool
    this.server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'query',
          description: 'Execute a SELECT query on Supabase',
          inputSchema: {
            type: 'object',
            properties: {
              table: {
                type: 'string',
                description: 'Table name to query',
              },
              select: {
                type: 'string',
                description: 'Columns to select (default: *)',
                default: '*',
              },
              filters: {
                type: 'array',
                description: 'Array of filters to apply',
                items: {
                  type: 'object',
                  properties: {
                    column: { type: 'string' },
                    operator: { 
                      type: 'string',
                      enum: ['eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'like', 'ilike', 'in']
                    },
                    value: { type: ['string', 'number', 'boolean', 'array'] }
                  },
                  required: ['column', 'operator', 'value']
                }
              },
              limit: {
                type: 'number',
                description: 'Limit number of results',
              },
              order: {
                type: 'object',
                properties: {
                  column: { type: 'string' },
                  ascending: { type: 'boolean', default: true }
                }
              }
            },
            required: ['table'],
          },
        },
        {
          name: 'insert',
          description: 'Insert data into a Supabase table',
          inputSchema: {
            type: 'object',
            properties: {
              table: {
                type: 'string',
                description: 'Table name to insert into',
              },
              data: {
                type: ['object', 'array'],
                description: 'Data to insert (single object or array of objects)',
              },
              returning: {
                type: 'boolean',
                description: 'Return inserted data',
                default: true,
              }
            },
            required: ['table', 'data'],
          },
        },
        {
          name: 'update',
          description: 'Update data in a Supabase table',
          inputSchema: {
            type: 'object',
            properties: {
              table: {
                type: 'string',
                description: 'Table name to update',
              },
              data: {
                type: 'object',
                description: 'Data to update',
              },
              filters: {
                type: 'array',
                description: 'Filters to identify rows to update',
                items: {
                  type: 'object',
                  properties: {
                    column: { type: 'string' },
                    operator: { type: 'string' },
                    value: { type: ['string', 'number', 'boolean'] }
                  },
                  required: ['column', 'operator', 'value']
                }
              },
              returning: {
                type: 'boolean',
                description: 'Return updated data',
                default: true,
              }
            },
            required: ['table', 'data', 'filters'],
          },
        },
        {
          name: 'delete',
          description: 'Delete data from a Supabase table',
          inputSchema: {
            type: 'object',
            properties: {
              table: {
                type: 'string',
                description: 'Table name to delete from',
              },
              filters: {
                type: 'array',
                description: 'Filters to identify rows to delete',
                items: {
                  type: 'object',
                  properties: {
                    column: { type: 'string' },
                    operator: { type: 'string' },
                    value: { type: ['string', 'number', 'boolean'] }
                  },
                  required: ['column', 'operator', 'value']
                }
              },
              returning: {
                type: 'boolean',
                description: 'Return deleted data',
                default: true,
              }
            },
            required: ['table', 'filters'],
          },
        },
        {
          name: 'rpc',
          description: 'Call a Supabase RPC function',
          inputSchema: {
            type: 'object',
            properties: {
              function_name: {
                type: 'string',
                description: 'Name of the RPC function',
              },
              params: {
                type: 'object',
                description: 'Parameters to pass to the function',
                default: {},
              }
            },
            required: ['function_name'],
          },
        },
      ],
    }));
    
    // Handle tool calls
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        switch (name) {
          case 'query':
            return await this.handleQuery(args);
          case 'insert':
            return await this.handleInsert(args);
          case 'update':
            return await this.handleUpdate(args);
          case 'delete':
            return await this.handleDelete(args);
          case 'rpc':
            return await this.handleRpc(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    });
  }
  
  async handleQuery(args) {
    let query = this.supabase.from(args.table).select(args.select || '*');
    
    // Apply filters
    if (args.filters) {
      for (const filter of args.filters) {
        query = query[filter.operator](filter.column, filter.value);
      }
    }
    
    // Apply limit
    if (args.limit) {
      query = query.limit(args.limit);
    }
    
    // Apply order
    if (args.order) {
      query = query.order(args.order.column, { ascending: args.order.ascending ?? true });
    }
    
    const { data, error } = await query;
    
    if (error) throw error;
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }
  
  async handleInsert(args) {
    const query = this.supabase.from(args.table).insert(args.data);
    
    if (args.returning) {
      query.select();
    }
    
    const { data, error } = await query;
    
    if (error) throw error;
    
    return {
      content: [
        {
          type: 'text',
          text: args.returning ? JSON.stringify(data, null, 2) : 'Insert successful',
        },
      ],
    };
  }
  
  async handleUpdate(args) {
    let query = this.supabase.from(args.table).update(args.data);
    
    // Apply filters
    for (const filter of args.filters) {
      query = query[filter.operator](filter.column, filter.value);
    }
    
    if (args.returning) {
      query.select();
    }
    
    const { data, error } = await query;
    
    if (error) throw error;
    
    return {
      content: [
        {
          type: 'text',
          text: args.returning ? JSON.stringify(data, null, 2) : 'Update successful',
        },
      ],
    };
  }
  
  async handleDelete(args) {
    let query = this.supabase.from(args.table).delete();
    
    // Apply filters
    for (const filter of args.filters) {
      query = query[filter.operator](filter.column, filter.value);
    }
    
    if (args.returning) {
      query.select();
    }
    
    const { data, error } = await query;
    
    if (error) throw error;
    
    return {
      content: [
        {
          type: 'text',
          text: args.returning ? JSON.stringify(data, null, 2) : 'Delete successful',
        },
      ],
    };
  }
  
  async handleRpc(args) {
    const { data, error } = await this.supabase.rpc(args.function_name, args.params || {});
    
    if (error) throw error;
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }
  
  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };
  }
  
  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Supabase MCP server running');
  }
}

const server = new SupabaseMCPServer();
server.run().catch(console.error);