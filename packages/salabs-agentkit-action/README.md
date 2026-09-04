# 🦾 SALabs Coinbase AgentKit Action Provider (`@quanxs/salabs-agentkit-action`)

[![NPM Version](https://img.shields.io/npm/v/@quanxs/salabs-agentkit-action.svg?style=flat-square&color=cb3837)](https://www.npmjs.com/package/@quanxs/salabs-agentkit-action)
[![Base Mainnet](https://img.shields.io/badge/Base%20Mainnet-0x154384Fb...-0052ff.svg?style=flat-square)](https://basescan.org/address/0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49)
[![AgentKit Compatible](https://img.shields.io/badge/Coinbase%20AgentKit-v0.1%2B-blue.svg?style=flat-square)](https://github.com/coinbase/agentkit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

Official **Coinbase AgentKit Action Provider** for **Quanxs SA Labs (SALABS)**.  
Equip any autonomous on-chain AI agent on Base with sub-2ms Lie $SE(3)$ Bishop Frame 3D Articulated Robotics CAD generation, watertight manifold solving, and automated x402 micro-settlement.

- **Base Registry Contract**: [`0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49`](https://basescan.org/address/0x154384Fb1BA2EB6570B8B6A016798bC9Dc064b49)
- **Master Treasury Payee**: [`0xA3f65F1C005528507e9E0E2E17cCC946f671c9d2`](https://basescan.org/address/0xA3f65F1C005528507e9E0E2E17cCC946f671c9d2)
- **Official Web Cockpit**: [https://salabs.quanxs.com/agora/deploy](https://salabs.quanxs.com/agora/deploy)

---

## ⚡ Installation

```bash
npm install @quanxs/salabs-agentkit-action
```

---

## 🤖 Usage with Coinbase AgentKit

```typescript
import { AgentKit, cdpWalletProvider } from "@coinbase/agentkit";
import { salabsActionProvider } from "@quanxs/salabs-agentkit-action";

// 1. Initialize CDP Wallet on Base Mainnet
const walletProvider = await cdpWalletProvider({
  apiKeyName: process.env.CDP_API_KEY_NAME,
  apiKeyPrivateKey: process.env.CDP_API_KEY_PRIVATE_KEY,
  networkId: "base-mainnet"
});

// 2. Add SALabs Action Provider to AgentKit
const agentKit = await AgentKit.from({
  walletProvider,
  actionProviders: [
    salabsActionProvider({
      autoSettle: true // Automatically route 0.1 USDC to SALabs Master Treasury
    })
  ]
});

// Now your agent can autonomously generate 3D CAD assemblies and verify manifold physics!
```

---

## 🛠️ Actions Provided

### 1. `salabs_generate_robotics_cad`
- **Description**: Generates a watertight manifold 3D CAD assembly in < 2ms using Type-2 Bishop Frame differential geometry. Euler characteristic $\chi = 0$.
- **Inputs**: `prompt` (string), `curve_scale` (number, default: 1.25)
- **Output**: Assembly components (Spine, Motor Hub, Mounting Flanges, Clevis Fork Joint), vertex & face counts, and full OBJ mesh string.

### 2. `salabs_query_onchain_registry`
- **Description**: Queries the Base Mainnet `SalabsAgoraRegistry` smart contract for tool pricing, active status, and treasury payee information.
- **Inputs**: `slug` (string)

### 3. `salabs_get_payment_specification`
- **Description**: Retrieves the x402 micropayment protocol parameters and Base Mainnet settlement addresses.

---

## 📜 Standalone Usage (Zero External Dependencies)

You can also use the analytical Lie $SE(3)$ Bishop Frame CAD generator directly without AgentKit:

```typescript
import { SalabsArticulatedRoboticsGenerator } from "@quanxs/salabs-agentkit-action";

const cad = SalabsArticulatedRoboticsGenerator.generateMesh(
  "18-DoF bipedal robotic knee joint actuator",
  1.25
);

console.log(`Generated in ${cad.latency_ms}ms with Euler char χ = ${cad.euler_characteristic}`);
console.log(cad.obj_format);
```

---

## 📜 License

MIT License © 2026 Team Sequence Thaumaturge & Quanxs SA Labs (SALABS).  
Main Domain: [https://quanxs.com](https://quanxs.com) | Portal: [https://salabs.quanxs.com](https://salabs.quanxs.com)
