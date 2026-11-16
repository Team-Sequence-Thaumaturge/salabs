FROM node:20-alpine

WORKDIR /app

COPY agora/ ./agora/
COPY tools/ ./tools/

ENTRYPOINT ["node", "/app/agora/mcp-agora-server.js"]
