// x402_agent_payment_gate.js
// Agentic Commerce Module: Live HTTP 402 Payment Gate, ZK Proof Generation, and Settlement Streams

/**
 * Parses a live HTTP 402 Payment Required header.
 * Expected format: 'L402 macaroon="...", invoice="..."'
 * @param {string} headerString - The HTTP header string.
 * @returns {object|null} Parsed header object with macaroon and invoice, or null if invalid.
 */
export function parse402Header(headerString) {
  if (!headerString || !headerString.startsWith('L402')) {
    return null;
  }

  const macaroonMatch = headerString.match(/macaroon="([^"]+)"/);
  const invoiceMatch = headerString.match(/invoice="([^"]+)"/);

  if (macaroonMatch && invoiceMatch) {
    return {
      macaroon: macaroonMatch[1],
      invoice: invoiceMatch[1]
    };
  }
  return null;
}

/**
 * Generates an HMAC-SHA256 signature for a given payload using the Web Crypto API.
 * @param {string} payload - The message to sign.
 * @param {string} secret - The secret key.
 * @returns {Promise<string>} Hex string of the signature.
 */
export async function generateSignature(payload, secret) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    enc.encode(payload)
  );
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Generates a zero-dependency client-side cryptographic proof (simulated ZK proof).
 * In this sandbox simulation, it hashes the identityHash to represent the proof.
 * @param {string} identityHash - The base identity string.
 * @returns {Promise<object>} An object containing the proof and timestamp.
 */
export async function generateZKProof(identityHash) {
  const enc = new TextEncoder();
  const data = enc.encode(identityHash + Date.now().toString());
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const proofHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  return {
    proof: `zkp_${proofHex.substring(0, 32)}`,
    timestamp: Date.now(),
    isValid: true
  };
}

/**
 * Streams micro-transactions simulating a continuous payment settlement stream.
 * @param {number} totalAmount - The total amount to settle.
 * @param {number} rate - Amount to settle per tick.
 * @param {function} callback - Function called on each tick: callback({ settled, remaining, status }).
 * @returns {function} A function to stop the stream early.
 */
export function simulateSettlementStream(totalAmount, rate, callback) {
  let settled = 0;

  const intervalId = setInterval(() => {
    settled += rate;
    if (settled >= totalAmount) {
      settled = totalAmount;
      clearInterval(intervalId);
      callback({ settled, remaining: 0, status: 'completed' });
    } else {
      callback({ settled, remaining: totalAmount - settled, status: 'streaming' });
    }
  }, 1000);

  return function stopStream() {
    clearInterval(intervalId);
    callback({ settled, remaining: totalAmount - settled, status: 'stopped' });
  };
}
