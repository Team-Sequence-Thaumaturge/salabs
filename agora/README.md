# 🏛️ SALabs Agora MCP Server (`@quanxs/salabs-agora-mcp`)

[![NPM Version](https://img.shields.io/npm/v/@quanxs/salabs-agora-mcp.svg?style=flat-square&color=cb3837)](https://www.npmjs.com/package/@quanxs/salabs-agora-mcp)
[![NPM Downloads](https://img.shields.io/npm/dt/@quanxs/salabs-agora-mcp.svg?style=flat-square)](https://www.npmjs.com/package/@quanxs/salabs-agora-mcp)
[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-blue.svg?style=flat-square)](https://modelcontextprotocol.io/)
[![Base Mainnet](https://img.shields.io/badge/Base%20Mainnet-0x154384Fb...-0052ff.svg?style=flat-square)](https://basescan.org/address/0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> **Official Model Context Protocol (MCP) Server for Quanxs SA Labs (SALABS)**  
> 0.02s Lie $SE(3)$ Bishop Frame 3D Articulated Robotics CAD Engine + 580+ Autonomous Developer Utilities Suite + x402 Micropayment Protocol on Base Mainnet.

- **NPM Package**: [`@quanxs/salabs-agora-mcp`](https://www.npmjs.com/package/@quanxs/salabs-agora-mcp)
- **Base Registry Contract**: [`0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49`](https://basescan.org/address/0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49)
- **Official Portal & Web Cockpit**: [https://salabs.quanxs.com/agora/](https://salabs.quanxs.com/agora/)

---

## ⚡ Key Capabilities & Tools

### 1. `generate_articulated_robotics_cad` (Sub-2ms Flagship 3D Geometry)
- Procedurally computes watertight manifold 3D CAD assemblies (Spine, Motor Hub, Mounting Flanges, Clevis Fork Joint) in < 2ms using Type-2 Bishop Frame continuous differential geometry.
- Guaranteed Euler Characteristic chi = 0 with 0 non-manifold edges (100% 3D printable manifold).
- Exports standard `.obj` mesh strings and multi-body robotics URDF/SDF structures.

### 2. `search_salabs_utilities` (580+ Tool Catalog Discovery)
- Instant sub-millisecond search across 580+ client-side developer utilities across 8 domains: Audio DSP, Cryptography/Security, 3D Spatial CAD, Text/Data Parsing, Image Graphics, and Mathematics.

### 3. `get_salabs_utility_info` (Tool Specs & Live URLs)
- Complete execution parameter schemas, category metadata, and direct live web URLs (`https://salabs.quanxs.com/tools/[slug].html`).

### 4. `execute_salabs_utility` (V8 Isolated Sandbox Execution & Code Extractor)
- Runs client-side utility algorithms locally in an isolated Node.js V8 virtual DOM sandbox.
- Or extracts pure JavaScript algorithms (`action: "extract_code"`) directly for AI code synthesis.

### 5. `get_x402_payment_specification` (M2M Agentic Micropayments)
- Standardized HTTP 402 payment specifications for autonomous AI-to-AI transactions over Base EVM and Solana networks directly routed to verified master payee wallets.

---

## 🚀 Quick Start (Zero Installation)

Run directly with `npx` in any terminal or agent workspace:

```bash
npx -y @quanxs/salabs-agora-mcp
```

Or install globally:

```bash
npm install -g @quanxs/salabs-agora-mcp
```

---

## 🛠️ MCP Client Configuration

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "salabs-agora": {
      "command": "npx",
      "args": ["-y", "@quanxs/salabs-agora-mcp"]
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
      "args": ["-y", "@quanxs/salabs-agora-mcp"]
    }
  }
}
```

### Windsurf & Devin (`mcp_config.json`)

```json
{
  "mcpServers": {
    "salabs-agora": {
      "command": "npx",
      "args": ["-y", "@quanxs/salabs-agora-mcp"]
    }
  }
}
```

---

## ⛓️ On-Chain Smart Contract Registry

- **Network**: Base Mainnet (Chain ID `8453`, EIP-4844)
- **Contract Address**: `0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49`
- **Basescan Explorer**: [https://basescan.org/address/0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49](https://basescan.org/address/0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49)
- **1-Click Web Cockpit**: [https://salabs.quanxs.com/agora/deploy](https://salabs.quanxs.com/agora/deploy)

---

## 📜 License

MIT License © 2026 Team Sequence Thaumaturge & Quanxs SA Labs (SALABS).  
Main Domain: [https://quanxs.com](https://quanxs.com) | Portal: [https://salabs.quanxs.com](https://salabs.quanxs.com)
