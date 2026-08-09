# ⚡ SAIR 1-Click Auto Injector v1.0.0

Omnipresent Chrome Extension (Manifest v3) for **1-Click Automatic Injection of SAIR 487-Substyle Tensor Specification Prompts and C++ Rendered PNG Image Style References** into Web AI Applications.

---

### 🌟 Supported AI Web Applications
- **Google Flow** (`labs.google/fx`) — Slate.js Editor Engine
- **ChatGPT** (`chatgpt.com`) — React Controlled Textarea
- **Claude** (`claude.ai`) — Contenteditable ProseMirror
- **Jules** — Multi-target CodeMirror / Rich Textarea
- **Google Gemini** (`gemini.google.com`) — Custom Web Component Editor

---

### 📦 Key Features
1. **Zero-CSP Base64 Data URI to Blob Engine**: Pure in-memory PNG image payload conversion.
2. **Slate.js Specification Compliant Injector**: Mutates native `TextNode.nodeValue` directly without destroying React WeakMap node tracking.
3. **3-Stage Double Text Guard Pipeline**: 
   - 0ms: Text Injection
   - 150ms: PNG Image Style Reference Paste
   - 350ms: Re-verify text presence in editor AST
4. **Slate Caret Activation (`selectionchange`)**: Forces Slate `editor.selection` to activate blinking caret ("딸깍") automatically without manual user clicks.

---

### 🔧 Extension Manifest Overview (`manifest.json`)
```json
{
  "manifest_version": 3,
  "name": "SAIR 1-Click Auto Injector",
  "version": "1.0.0",
  "permissions": [
    "tabs",
    "activeTab",
    "scripting",
    "storage",
    "clipboardRead",
    "clipboardWrite"
  ]
}
```

© 2026 **Team Sequence Thaumaturge**.
