#!/usr/bin/env node
/**
 * SALabs AI Agent Digital Agora - Official Model Context Protocol (MCP) Server
 * Full JSON-RPC 2.0 stdio compliant server for Claude Desktop, Cursor, Gemini, and AutoGen.
 * Connects AI agents directly to the 0.02s 3D CAD Engine AND 580+ Developer Utilities Suite.
 */

import readline from 'readline';
import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';
import { SalabsArticulatedRoboticsGenerator } from './salabs-spatial-engine.js';
import { SalabsX402Gateway } from './x402-payment-gateway.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load 580+ Tools Catalog
let TOOLS_CATALOG = [];
try {
  const catalogPath = path.join(__dirname, 'salabs-tools-catalog.json');
  if (fs.existsSync(catalogPath)) {
    TOOLS_CATALOG = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
  }
} catch (e) {
  TOOLS_CATALOG = [];
}

/**
 * Executes or extracts code from any of the 580+ client-side utility tools.
 */
async function executeToolLogic(slug, rawParams = {}, action = 'execute') {
  const cleanSlug = (slug || '').replace(/\.html$/, '').toLowerCase().trim();
  const liveUrl = `https://salabs.quanxs.com/tools/${cleanSlug}.html`;
  const toolsDir = path.join(__dirname, '..', 'tools');
  const filePath = path.join(toolsDir, cleanSlug + '.html');

  let html = '';
  if (fs.existsSync(filePath)) {
    html = fs.readFileSync(filePath, 'utf8');
  } else {
    try {
      const resp = await fetch(liveUrl);
      if (resp.ok) {
        html = await resp.text();
      }
    } catch (e) {
      // Fallback failed
    }
  }

  if (!html) {
    return {
      status: 'NOT_FOUND',
      error: `Tool '${cleanSlug}' not found in SALabs 580+ catalog. Use 'search_salabs_utilities' to discover tools.`
    };
  }

  // 1. Extract input & textarea IDs
  const inputIds = [];
  const inputRegex = /<(?:input|textarea)\b[^>]*\bid=["']([^"']+)["'][^>]*>/gi;
  let m;
  while ((m = inputRegex.exec(html)) !== null) {
    inputIds.push(m[1]);
  }

  // 2. Extract button onclick handlers
  const buttonTriggers = [];
  const btnRegex = /<button\b[^>]*\bonclick=["']([a-zA-Z0-9_$]+)\([^)]*\)["'][^>]*>/gi;
  while ((m = btnRegex.exec(html)) !== null) {
    if (!buttonTriggers.includes(m[1])) {
      buttonTriggers.push(m[1]);
    }
  }

  // 3. Extract main scripts (excluding Google AdSense and Schema.org JSON-LD)
  const scriptRegex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let scriptCode = '';
  while ((m = scriptRegex.exec(html)) !== null) {
    const attrs = m[1];
    const code = m[2].trim();
    if (!attrs.includes('application/ld+json') && !attrs.includes('adsbygoogle') && !code.includes('adsbygoogle')) {
      scriptCode += code + '\n';
    }
  }

  if (action === 'extract_code') {
    return {
      status: 'EXTRACTED',
      slug: cleanSlug,
      input_fields: inputIds,
      triggers: buttonTriggers,
      extracted_javascript: scriptCode,
      live_direct_url: liveUrl
    };
  }

  if (action === 'inspect') {
    return {
      status: 'INSPECTED',
      slug: cleanSlug,
      input_fields: inputIds,
      triggers: buttonTriggers,
      live_direct_url: liveUrl
    };
  }

  // Parameter binding
  const elementValues = {};
  for (const id of inputIds) {
    if (rawParams[id] !== undefined) {
      elementValues[id] = String(rawParams[id]);
    }
  }
  // Fallback auto-binding: map generic keys like text, input, prompt, or first argument
  if (inputIds.length > 0 && Object.keys(elementValues).length === 0) {
    const val = rawParams.text || rawParams.input || rawParams.data || rawParams.prompt || Object.values(rawParams)[0];
    if (val !== undefined) {
      elementValues[inputIds[0]] = String(val);
    }
  }

  const mockElements = {};
  for (const id of inputIds) {
    mockElements[id] = {
      value: elementValues[id] || '',
      innerHTML: elementValues[id] || '',
      textContent: elementValues[id] || ''
    };
  }

  const mockDoc = {
    getElementById: (id) => {
      if (!mockElements[id]) {
        mockElements[id] = { value: '', innerHTML: '', textContent: '' };
      }
      return mockElements[id];
    }
  };

  const sandbox = {
    document: mockDoc,
    window: { crypto: globalThis.crypto },
    console: { log: () => {}, warn: () => {}, error: () => {} },
    TextEncoder: globalThis.TextEncoder,
    TextDecoder: globalThis.TextDecoder,
    btoa: (str) => Buffer.from(str, 'binary').toString('base64'),
    atob: (b64) => Buffer.from(b64, 'base64').toString('binary'),
    alert: () => {}
  };

  vm.createContext(sandbox);
  try {
    vm.runInContext(scriptCode, sandbox, { timeout: 2000 });
  } catch (err) {
    return {
      status: 'WEB_INTERACTIVE',
      slug: cleanSlug,
      note: 'Tool relies on browser-only interactive WebAudio or Canvas hardware rendering.',
      live_direct_url: liveUrl,
      extracted_code: scriptCode.slice(0, 500)
    };
  }

  // Trigger button operations
  for (const trigger of buttonTriggers) {
    if (typeof sandbox[trigger] === 'function') {
      try {
        const ret = sandbox[trigger]();
        if (ret && typeof ret.then === 'function') {
          await ret;
        }
      } catch (err) {
        // Fallback gracefully
      }
    }
  }

  const results = {};
  for (const [id, el] of Object.entries(mockElements)) {
    results[id] = el.value || el.textContent || el.innerHTML;
  }

  return {
    status: 'SUCCESS',
    slug: cleanSlug,
    live_direct_url: liveUrl,
    inputs: elementValues,
    outputs: results
  };
}

export const MCP_MANIFEST = {
  name: "salabs-agora-master-mcp",
  version: "2.1.0",
  description: "Official MCP Server for SALabs Sovereign 3D Spatial Geometry & 580+ Autonomous Developer Utilities Hub",
  vendor: "Quanxs SA Labs (SALABS)",
  homepage: "https://salabs.quanxs.com/agora/",
  tools: [
    {
      name: "generate_articulated_robotics_cad",
      description: "Generates a high-precision, watertight manifold 3D CAD assembly (Spine, MotorHub, Flanges, ClevisFork) in < 2ms using Type-2 Bishop Frame differential geometry. Euler characteristic chi = 0.",
      inputSchema: {
        type: "object",
        properties: {
          prompt: {
            type: "string",
            description: "Industrial robotics or spatial component prompt (e.g., '18-DoF bipedal robotic knee joint actuator with servo housing')"
          },
          curve_scale: {
            type: "number",
            description: "Spatial curvature radius scale (default: 1.25)",
            default: 1.25
          }
        },
        required: ["prompt"]
      }
    },
    {
      name: "search_salabs_utilities",
      description: "Searches through SALabs catalog of 580+ specialized developer utilities across Audio DSP, Security/Crypto, 3D Spatial CAD, Image Graphics, and Text Parsing. Returns matched tools with direct live URLs.",
      inputSchema: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Search keyword (e.g., 'audio', 'hash', 'binaural', 'cad', 'diff', 'biquad', 'ascii', 'jwt')"
          },
          category: {
            type: "string",
            description: "Optional category filter: audio_dsp_spatial, security_crypto, image_graphics, spatial_3d_cad, text_data_parsing, math_scientific, frontend_web, general_utilities"
          },
          limit: {
            type: "number",
            description: "Maximum results to return (default: 10, max: 50)",
            default: 10
          }
        }
      }
    },
    {
      name: "get_salabs_utility_info",
      description: "Retrieves complete execution details, live web access URL, and description for any specific utility among the 580+ SALabs tools.",
      inputSchema: {
        type: "object",
        properties: {
          slug: {
            type: "string",
            description: "The unique slug identifier of the tool (e.g., 'audio-binaural-beats-studio', 'ascii-art-text-generator', 'api-mock-sandbox')"
          }
        },
        required: ["slug"]
      }
    },
    {
      name: "execute_salabs_utility",
      description: "Directly executes any utility among the 580+ SALabs tool suite in an isolated V8 sandbox, or extracts its clean JavaScript mathematical algorithm for AI code synthesis. Supports audio DSP, cryptographic hashing/ciphers, 3D spatial transforms, text parsing, and data conversion.",
      inputSchema: {
        type: "object",
        properties: {
          slug: {
            type: "string",
            description: "The unique slug identifier of the tool (e.g., 'ascii-art-text-generator', 'crypto-aes-cbc-pbkdf2-encryptor', 'audio-binaural-beats-studio')"
          },
          parameters: {
            type: "object",
            description: "Input parameters / key-value arguments for the tool (e.g., {'text': 'SALABS'}, {'pass-in': 'secret', 'plain-in': 'data'})",
            default: {}
          },
          action: {
            type: "string",
            description: "Action to perform: 'execute' (runs tool locally in sandbox), 'extract_code' (returns pure JS algorithm code), or 'inspect' (returns schema and live URL)",
            enum: ["execute", "extract_code", "inspect"],
            default: "execute"
          }
        },
        required: ["slug"]
      }
    },
    {
      name: "get_x402_payment_specification",
      description: "Returns the official x402 machine-to-machine micropayment specification and payee wallets for autonomous AI settlements.",
      inputSchema: {
        type: "object",
        properties: {}
      }
    }
  ]
};

export class SalabsMcpServer {
  static async handleCall(toolName, args = {}) {
    // 1. Flagship 3D CAD Generator
    if (toolName === "generate_articulated_robotics_cad") {
      const prompt = args.prompt || "High-precision robotic actuator joint";
      const scale = typeof args.curve_scale === "number" ? args.curve_scale : 1.25;
      const mesh = SalabsArticulatedRoboticsGenerator.generateMesh(prompt, scale);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              status: "SUCCESS",
              engine: "SALabs Jules v9 Bishop Frame Continuum Solver",
              prompt: mesh.prompt,
              latency_ms: mesh.latency_ms,
              euler_characteristic: mesh.euler_characteristic,
              non_manifold_edges: mesh.non_manifold_edges,
              assembly_components: mesh.assembly_components,
              stats: mesh.stats,
              preview_obj_snippet: mesh.obj_format.split("\n").slice(0, 25).join("\n") + "\n# ... (full mesh payload included)"
            }, null, 2)
          }
        ]
      };
    }

    // 2. Search 580+ Utilities
    if (toolName === "search_salabs_utilities") {
      const query = (args.query || "").toLowerCase().trim();
      const category = (args.category || "").toLowerCase().trim();
      const limit = Math.min(50, Math.max(1, args.limit || 10));

      let matched = TOOLS_CATALOG;
      if (category) {
        matched = matched.filter(t => t.category.toLowerCase().includes(category));
      }
      if (query) {
        matched = matched.filter(t => 
          t.slug.toLowerCase().includes(query) ||
          t.title.toLowerCase().includes(query) ||
          t.description.toLowerCase().includes(query)
        );
      }

      const results = matched.slice(0, limit);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              total_catalog_size: TOOLS_CATALOG.length,
              matched_count: matched.length,
              returned_results: results.length,
              tools: results
            }, null, 2)
          }
        ]
      };
    }

    // 3. Get Specific Tool Info
    if (toolName === "get_salabs_utility_info") {
      const slug = (args.slug || "").replace(/\.html$/, '').toLowerCase().trim();
      const found = TOOLS_CATALOG.find(t => t.slug.toLowerCase() === slug);
      if (!found) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                status: "NOT_FOUND",
                message: `Tool with slug '${slug}' not found in 580+ SALabs catalog. Use 'search_salabs_utilities' to discover tools.`
              }, null, 2)
            }
          ]
        };
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              status: "FOUND",
              tool: found,
              live_direct_url: found.url,
              execution_mode: "Client-side Zero-Latency Web Utility"
            }, null, 2)
          }
        ]
      };
    }

    // 4. Master Execute Utility Tool (Supports execute_salabs_utility & salabs_execute_utility)
    if (toolName === "execute_salabs_utility" || toolName === "salabs_execute_utility") {
      const slug = args.slug;
      const params = args.parameters || {};
      const action = args.action || "execute";
      const execResult = await executeToolLogic(slug, params, action);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(execResult, null, 2)
          }
        ]
      };
    }

    // 5. x402 Micropayment Specification
    if (toolName === "get_x402_payment_specification") {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(SalabsX402Gateway.CONFIG, null, 2)
          }
        ]
      };
    }

    throw new Error(`Tool '${toolName}' not found on SALabs Agora MCP Server.`);
  }

  static async processJsonRpc(msg) {
    const { id, method, params } = msg;

    if (method === "initialize") {
      return {
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: {
            name: MCP_MANIFEST.name,
            version: MCP_MANIFEST.version
          }
        }
      };
    }

    if (method === "notifications/initialized") return null;

    if (method === "tools/list") {
      return {
        jsonrpc: "2.0",
        id,
        result: { tools: MCP_MANIFEST.tools }
      };
    }

    if (method === "tools/call") {
      try {
        const toolName = params?.name;
        const toolArgs = params?.arguments || {};
        const callResult = await this.handleCall(toolName, toolArgs);
        return { jsonrpc: "2.0", id, result: callResult };
      } catch (err) {
        return {
          jsonrpc: "2.0",
          id,
          error: { code: -32603, message: err.message }
        };
      }
    }

    if (method === "ping") {
      return { jsonrpc: "2.0", id, result: {} };
    }

    return {
      jsonrpc: "2.0",
      id,
      error: { code: -32601, message: `Method '${method}' not found.` }
    };
  }
}

// Standalone CLI execution test
if (process.argv[2] === "test") {
  console.log("=== Testing SALabs 580+ Tools Search & Execution ===");
  const testRes = await SalabsMcpServer.handleCall("search_salabs_utilities", { query: "crypto", limit: 2 });
  console.log("Search Result:\n", testRes.content[0].text);

  const execRes = await SalabsMcpServer.handleCall("execute_salabs_utility", {
    slug: "ascii-art-text-generator",
    parameters: { text: "SALABS" }
  });
  console.log("Execution Result:\n", execRes.content[0].text);
} else {
  // Stdio JSON-RPC stream listener for Claude Desktop & Cursor
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  rl.on('line', async (line) => {
    if (!line || !line.trim()) return;
    try {
      const msg = JSON.parse(line);
      const resp = await SalabsMcpServer.processJsonRpc(msg);
      if (resp) process.stdout.write(JSON.stringify(resp) + "\n");
    } catch (e) {
      process.stdout.write(JSON.stringify({
        jsonrpc: "2.0",
        id: null,
        error: { code: -32700, message: "Parse error: " + e.message }
      }) + "\n");
    }
  });
}
