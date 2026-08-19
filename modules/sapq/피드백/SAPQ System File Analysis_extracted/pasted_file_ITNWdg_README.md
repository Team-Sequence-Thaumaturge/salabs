# Quanxs SALabs Open Source Utilities & Engines

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![WebGL / Three.js](https://img.shields.io/badge/WebGL-Three.js-black?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
[![WebAudio API](https://img.shields.io/badge/WebAudio-API-purple?style=for-the-badge)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
[![AST Auditor](https://img.shields.io/badge/QA-SAPQ%20AST%20Auditor-00f2fe?style=for-the-badge)](https://github.com/Team-Sequence-Thaumaturge/Salabs-Open-source)
[![AI Copilot](https://img.shields.io/badge/AI-Sovereign%20CoPilot%20(SACP)-ff0055?style=for-the-badge)](https://github.com/Team-Sequence-Thaumaturge/Salabs-Open-source)
[![Reliability](https://img.shields.io/badge/Reliability-0--Runtime--Crash-gold?style=for-the-badge)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](https://github.com/Team-Sequence-Thaumaturge/Salabs-Open-source/pulls)

Welcome to the official **SALabs Open Source Repository**. This repository contains a collection of clean, open-source developer utilities, 3D graphics rendering engines, quality control auditors, and autonomous copilot protocols developed by Team Sequence Thaumaturge.

---

## 🏛️ Repository Contents

### 1. 🛡️ Sequence Autonomic Parsing & QA (SAPQ) Engine (`/sapq`, `/multi_vector_parser.py`)
An advanced code integrity auditor designed to detect semantic contradictions, out-of-order execution, and incomplete mockup stubs (anti-mockup gate) in source code.
- **Torsion Crossing Detection**: Flags when variables, functions, or DOM IDs are referenced before their physical declaration.
- **Ghost Node Scanner**: Identifies isolated dead variables.
- **Anti-Mockup AST Audit**: Rejects code containing dummy/mock placeholders (e.g. `Math.random()`, incomplete timeout stubs).
- **DOM Event Target Mismatch Parser**: Static DOM Event listener parsing (`sapq_dom_relay.py`) to prevent `TypeError: Cannot read properties of null` runtime exceptions.
- **Cascade Mutation Graph**: Multi-file Cascade Mutation Dual-Graph Engine (`sapq_cascade_graph.py`) tracking domino side-effects across module refactoring.
- **Agent Self-Healing Sandbox**: Isolated HTTP Proxy Sandbox (`sapq_sandbox_proxy.py`) providing real-time line-level error traces to AI agents for 0-human self-healing code generation.
- **CLI & Web Visualizer**: Includes a CLI scanner (`python -m sapq.sapq_cli`) and a browser-based drag-and-drop HTML5 Canvas cockpit (`tools/jules-ai-qa-cross-parsing-auditor.html`).

### 2. 🤖 Sequence Autonomic Control Protocol (SACP) / Sovereign CoPilot (`/sacp`)
A clean, secure, and generic agentic copilot engine and file watcher protocol.
- **Sovereign CoPilot Core**: Asynchronous python loop engine and local directory observer (`sacp_copilot_engine.py`, `sacp_file_watcher.py`).
- **CoPilot Web Studio**: Beautiful interactive browser cockpit (`sacp_chat_studio.html`) and direct JSON-based chat stream configurations.
- **WASM Bridge**: Native C++ wasm bindings (`chrome_extension/sacp_wasm_bridge.cpp`) for high-performance agent-to-browser communication.

### 3. 🎨 Polyglot 3D Spatial Rendering Engine (`/polyglot_3d_engine`)
- Modular WebGL-based Three.js rendering library (`src/`) for building high-performance 120 FPS instanced mesh 3D simulations and spatial dynamics.

### 4. 🧰 420+ Pure Client-Side Utility Tools (`/tools`)
A comprehensive bundle of single-file browser utility tools. These run 100% locally with 0 server-side dependencies:
- **Audio utilities**: 200+ specialized audio tools (bpm metronome, binaural beats, parametric EQ, reverb convolver, granular synthethizer, voice pitch trackers).
- **Web Design utilities**: CSS box shadow inset studio, backdrop filter generator, clip-path generator, color contrast accessibility checkers.
- **Developer utilities**: Base64 JWT decoder, JS AST code complexity analyzer, client-side localstorage/session managers, mock API sandboxes.

---

## 🚀 Getting Started

### 🐍 Python Engines (SAPQ & SACP)
Prerequisites:
```bash
pip install requests psutil
```

Audit a target script using the SAPQ CLI:
```bash
python -m sapq.sapq_cli "path/to/target"
```

Start the SACP Sovereign CoPilot observer:
```bash
python -m sacp.sacp_copilot_engine --watch "path/to/watch/directory"
```

### 🌐 Web Tools
To use any of the 420+ browser utilities (including the SAPQ Code Auditor and SACP Chat Studio), simply open the respective `.html` file inside the `tools/` or `sacp/` directory in any modern web browser.

---

## 📜 SAPQ Engine Release Patch Notes (v1.0 ➔ v3.0 Timeline)

### 🟢 SAPQ v1.0 — Static AST & OS Safety Core (Phases 1 ~ 13)
- **Subprocess Popup Flashing Audit**: Automated detection of `creationflags=0x08000000` (`CREATE_NO_WINDOW`) for Python background subprocesses to prevent Windows CMD popups.
- **`os.system` Ban (`MOCKUP_HALLUCINATION`)**: Strictly flags `os.system` as an insecure mockup call and mandates `subprocess` usage.
- **Script Hoisting Engine**: Automatically hoists HTML `<script>` tags to the top of `<head>` during tool unpacking.

### 🔵 SAPQ v2.0 — Multi-Vector Cross-Parsing & OS Process Auditor (Phases 14 ~ 17)
- **4-Stage Cross-Parsing Protocol**: Enforces 4-directional cross-parsing ($A\to Z, Z\to A, a\to c\to e, z\to x\to v$).
- **`TORSION_CROSSING` & `GHOST_NODE` Detection**: Flags reverse dependency reference torsions and cleans isolated zombie variables before deployment.
- **Bitwise Mask Check**: Supports combined flag masks `(creationflags & 0x08000000) != 0` (e.g. `0x08000008` detached processes).
- **OS Daemon Duplication Audit**: Integrates `psutil` queries to detect background daemon duplicates and prevent memory/port collisions.

### 🟣 SAPQ v3.0 — DOM-Event Relay, Cascade Graph & Agent Sandbox (Phases 18 ~ 19)
- **DOM Target Mismatch Parser (`sapq_dom_relay.py`)**: Static DOM Event listener parsing to resolve `document.getElementById` target ID mismatches and eliminate runtime `TypeError: Cannot read properties of null` exceptions.
- **Cascade Mutation Graph (`sapq_cascade_graph.py`)**: Multi-file Cascade Mutation Dual-Graph Engine tracking domino side-effects across module refactoring.
- **Agent Self-Healing Sandbox (`sapq_sandbox_proxy.py`, `sapq_agent_protocol.py`)**: Isolated HTTP Proxy Sandbox providing real-time line-level error traces to AI agents (Jules/Spark/Antigravity) for 0-human self-healing code generation.
- **Preflight Sanity & Checkpoint Logging**: `sapq_preflight.py` and `sapq_checkpoint.py` logging for 0-runtime-crash deployments.

---

## 🏷️ Topics, Tags & Developer Keywords (SEO Index)

### 🔑 Tech Stack & Domain Tags
`#Python3` `#ASTParser` `#StaticAnalysis` `#CodeAuditor` `#WebGL` `#ThreeJS` `#WebAudioAPI` `#ChromeExtension` `#WASM` `#CppBindings` `#SelfHealingCode` `#AIAgent` `#LLMCopilot` `#QuantumSimulation` `#PostQuantumCrypto` `#WebXR` `#ClientSideTools` `#DeveloperUtilities` `#OpenSource` `#ZeroRuntimeCrash` `#Vercel` `#SALabs` `#TeamSequenceThaumaturge`

### 🔎 Search Queries & Discoverability Index
- **Static Code Analysis & AI Quality Control**: Python AST Parser, Static Code Auditor, Reverse Dependency Checker, Ghost Node Detector, Anti-Mockup Gate, Agentic Code Verification, Zero-Crash Code Deployments, Autonomous Self-Healing Pipeline.
- **Browser Utilities & Single-File Web Apps**: Pure JavaScript Client-Side Tools, Offline Web Tools, WebAudio Synthesizer, Binaural Beats Generator, Parametric EQ, WebGL 3D Particle Physics Engine, CSS Box Shadow Generator, Base64 JWT Claims Inspector, Post-Quantum Cryptography Studio.
- **Agentic Protocols & Extension Architecture**: Autonomous Agent Watcher, Sovereign CoPilot Engine, C++ WebAssembly Extension Bridge, Local Proxy Sandbox.

---

## 📄 License
Licensed under the **MIT License**. Feel free to use, modify, and distribute for personal or commercial projects.
