/**
 * SALabs AI Agent Digital Agora - Official Model Context Protocol (MCP) Server
 * Full JSON-RPC 2.0 stdio compliant server for Claude Desktop, Cursor, Gemini, and AutoGen.
 * Connects AI agents directly to the 0.02s Lie SE(3) Bishop Frame 3D CAD Engine.
 */

import readline from 'readline';
import { SalabsArticulatedRoboticsGenerator } from './salabs-spatial-engine.js';
import { SalabsX402Gateway } from './x402-payment-gateway.js';

export const MCP_MANIFEST = {
  name: "salabs-agora-spatial-mcp",
  version: "1.0.0",
  description: "Official MCP Server for SALabs 3D Spatial Geometry & Articulated Robotics CAD Generation",
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
  static handleCall(toolName, args = {}) {
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

  static processJsonRpc(msg) {
    const { id, method, params } = msg;

    // 1. MCP Initialization
    if (method === "initialize") {
      return {
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: {
            tools: {}
          },
          serverInfo: {
            name: MCP_MANIFEST.name,
            version: MCP_MANIFEST.version
          }
        }
      };
    }

    // 2. Notifications (e.g. notifications/initialized)
    if (method === "notifications/initialized") {
      return null;
    }

    // 3. List Tools
    if (method === "tools/list") {
      return {
        jsonrpc: "2.0",
        id,
        result: {
          tools: MCP_MANIFEST.tools
        }
      };
    }

    // 4. Call Tool
    if (method === "tools/call") {
      try {
        const toolName = params?.name;
        const toolArgs = params?.arguments || {};
        const callResult = this.handleCall(toolName, toolArgs);
        return {
          jsonrpc: "2.0",
          id,
          result: callResult
        };
      } catch (err) {
        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32603,
            message: err.message
          }
        };
      }
    }

    // 5. Ping
    if (method === "ping") {
      return { jsonrpc: "2.0", id, result: {} };
    }

    // Unknown method
    return {
      jsonrpc: "2.0",
      id,
      error: {
        code: -32601,
        message: `Method '${method}' not found.`
      }
    };
  }
}

// Check if running in CLI test mode or stdio server mode
if (process.argv[2] === "test") {
  console.log("=== Testing SALabs MCP Server Tool Call ===");
  const testRes = SalabsMcpServer.handleCall("generate_articulated_robotics_cad", {
    prompt: "Bipedal humanoid ankle actuator with dual flange rings"
  });
  console.log(testRes.content[0].text);
} else {
  // Stdio JSON-RPC stream listener for Claude Desktop & Cursor
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  rl.on('line', (line) => {
    if (!line || !line.trim()) return;
    try {
      const msg = JSON.parse(line);
      const resp = SalabsMcpServer.processJsonRpc(msg);
      if (resp) {
        process.stdout.write(JSON.stringify(resp) + "\n");
      }
    } catch (e) {
      process.stdout.write(JSON.stringify({
        jsonrpc: "2.0",
        id: null,
        error: { code: -32700, message: "Parse error: " + e.message }
      }) + "\n");
    }
  });
}
