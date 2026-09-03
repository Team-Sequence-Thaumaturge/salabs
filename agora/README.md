# SALabs Agora MCP Server (`salabs-agora-mcp`)

[![MCP Compatible](https://img.shields.io/badge/MCP-2024--11--05-blue.svg)](https://modelcontextprotocol.io/)
[![Version](https://img.shields.io/badge/Version-2.1.0-emerald.svg)](https://salabs.quanxs.com/agora/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Official Model Context Protocol (MCP) Server for Quanxs SA Labs (SALABS)**  
> 0.02s Lie SE(3) Bishop Frame 3D Articulated Robotics CAD Engine + 580+ Autonomous Developer Utilities Suite + x402 Micropayment Protocol.

---

## ⚡ Key Capabilities

1. **`generate_articulated_robotics_cad`** (1.12ms Flagship 3D Geometry)
   - Generates watertight manifold 3D CAD assemblies (Spine, Motor Hub, Mounting Flanges, Clevis Fork Joint) in < 2ms using Type-2 Bishop Frame differential geometry.
   - Euler Characteristic $\chi = 0$.

2. **`search_salabs_utilities`** (Catalog Discovery)
   - Instant search across 580+ client-side developer utilities across 8 domains: Audio DSP, Cryptography/Security, 3D Spatial CAD, Text Parsing, Image Graphics, and Mathematics.

3. **`get_salabs_utility_info`** (Tool Specs & Live Web Access)
   - Complete execution parameter schemas and direct live web URLs (`https://salabs.quanxs.com/tools/[slug].html`).

4. **`execute_salabs_utility`** (V8 Sandbox Execution & JS Code Extractor)
   - Runs client-side utility algorithms locally in an isolated Node.js V8 virtual DOM sandbox.
   - Or extracts clean pure JavaScript algorithms (`action: "extract_code"`) directly for AI code synthesis.
   - Automatically falls back to real-time remote fetching when run in minimal environments without local tool files.

5. **`get_x402_payment_specification`** (M2M Agentic Micropayments)
   - Standardized HTTP 402 payment specifications for autonomous AI-to-AI transactions over Base EVM and Solana.

---

## 🚀 Quick Start

### Run with `npx` (No Installation Needed)

```bash
npx salabs-agora-mcp
```

### Installation

```bash
npm install -g salabs-agora-mcp
```

---

## 🛠️ Client Configuration

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "salabs-agora": {
      "command": "npx",
      "args": ["-y", "salabs-agora-mcp"]
    }
  }
}
```

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "salabs-agora": {
      "command": "npx",
      "args": ["-y", "salabs-agora-mcp"]
    }
  }
}
```

### Google Antigravity (`~/.gemini/config/mcp_config.json`)

```json
{
  "mcpServers": {
    "salabs-agora": {
      "command": "npx",
      "args": ["-y", "salabs-agora-mcp"]
    }
  }
}
```

---

## 📜 License

MIT License © 2026 Team Sequence & Quanxs SA Labs (SALABS).
Official Portal: [https://salabs.quanxs.com/agora/](https://salabs.quanxs.com/agora/)
