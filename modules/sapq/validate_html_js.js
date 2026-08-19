const fs = require('fs');
const acorn = require('acorn');

const filePath = 'tools/jules-master-3d-spatial-engine-v1-2.html';
const htmlContent = fs.readFileSync(filePath, 'utf-8');

// Extract all <script> contents (ignoring application/ld+json and JSON-LD contexts)
const scriptRegex = /<script(?:\s+(?!type=["']application\/ld\+json["'])[^>]*)?>(.*?)<\/script>/gis;
let match;
let scripts = [];

while ((match = scriptRegex.exec(htmlContent)) !== null) {
  const content = match[1].trim();
  // Filter out any missed JSON blocks
  if (content.length > 0 && !content.startsWith('{') && !content.includes('"@context"')) {
    scripts.push(content);
  }
}

const jsCode = scripts.join('\n');

try {
  acorn.parse(jsCode, { ecmaVersion: 'latest', sourceType: 'module' });
  console.log('Syntax validation passed.');
  process.exit(0);
} catch (error) {
  console.error('Syntax error found in extracted JS:', error.message);
  process.exit(1);
}
