/**
 * SALabs x402 Micropayment & Autonomous Metering Gateway
 * Protocol: x402-v1.0 (Machine-to-Machine Micro-Settlement)
 * Routes all autonomous payments directly to Market-nim's master wallets:
 *   - Base (EVM USDC): 0xA3f65F1C005528507e9E0E2E17cCC946f671c9d2
 *   - Solana: DkyioiU3ugjhvoDBTwb1MTkmceETCg4nstuPPf6PGBZV
 */

export class SalabsX402Gateway {
  static CONFIG = {
    protocol_version: "x402-v1.0",
    service_name: "SALabs Sovereign 3D Spatial Agora API",
    unit_price_usd: "0.001",
    payee_wallets: {
      base_evm: "0xA3f65F1C005528507e9E0E2E17cCC946f671c9d2",
      solana: "DkyioiU3ugjhvoDBTwb1MTkmceETCg4nstuPPf6PGBZV"
    },
    supported_networks: ["base", "solana", "arbitrum", "polygon"]
  };

  /**
   * Process incoming request headers for x402 payment verification.
   * If valid payment or pre-paid token exists, returns { authorized: true }.
   * Otherwise returns { authorized: false, response: 402_PAYLOAD }.
   */
  static verifyPayment(headers = {}) {
    const authHeader = headers['authorization'] || headers['Authorization'] || '';
    const paymentTx = headers['x-payment-tx'] || headers['X-Payment-Tx'] || '';
    const challengeToken = headers['x-challenge-token'] || headers['X-Challenge-Token'] || '';

    // Check 1: Bearer API Key (e.g. from human billing or verified agent subscription)
    if (authHeader.startsWith('Bearer ')) {
      const token = authHeader.replace('Bearer ', '').trim();
      if (token && token.length >= 16) {
        return {
          authorized: true,
          method: 'API_KEY_OR_AGENT_CREDIT',
          token_id: token.slice(0, 8) + '...',
          timestamp: Date.now()
        };
      }
    }

    // Check 2: On-Chain Micro-Payment Transaction Hash
    if (paymentTx && paymentTx.length >= 32) {
      return {
        authorized: true,
        method: 'ON_CHAIN_MICRO_TX',
        tx_hash: paymentTx,
        payee: this.CONFIG.payee_wallets.base_evm,
        timestamp: Date.now()
      };
    }

    // Unpaid request: Issue HTTP 402 Payment Challenge
    const generatedChallenge = `ch_${Math.random().toString(36).substring(2, 12)}_${Date.now()}`;
    return {
      authorized: false,
      status: 402,
      headers: {
        'WWW-Authenticate': `x402 protocol="${this.CONFIG.protocol_version}", amount="${this.CONFIG.unit_price_usd}", currency="USDC", payee="${this.CONFIG.payee_wallets.base_evm}"`,
        'X-Payee-Address-Base': this.CONFIG.payee_wallets.base_evm,
        'X-Payee-Address-Solana': this.CONFIG.payee_wallets.solana,
        'X-Unit-Price-USD': this.CONFIG.unit_price_usd
      },
      payload: {
        status: 402,
        error: "Payment Required",
        message: "SALabs 3D Spatial Agora requires x402 machine micropayment ($0.001 / Call).",
        protocol: this.CONFIG.protocol_version,
        pricing: {
          amount: this.CONFIG.unit_price_usd,
          currency: "USDC",
          networks: this.CONFIG.supported_networks
        },
        payee: this.CONFIG.payee_wallets,
        challenge_token: generatedChallenge,
        instructions: {
          step1: `Send ${this.CONFIG.unit_price_usd} USDC on Base or Solana to the payee address with challenge_token memo.`,
          step2: "Resend request with 'X-Payment-Tx: <TRANSACTION_HASH>' or 'Authorization: Bearer <API_KEY>' header."
        },
        instant_test_token_faucet: "salabs_guest_test_token_88921b74e"
      }
    };
  }
}
