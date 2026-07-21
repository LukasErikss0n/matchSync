FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# NODE_ENV=production builds and serves the static/prerendered bundle via
# scripts/prod-server.mjs, which also proxies /api to the backend (so
# Googlebot's raw HTML gets per-route canonical/title tags AND the frontend's
# same-origin /api/* calls still reach the backend in production);
# anything else keeps the vite dev server with HMR for local development.
CMD ["sh", "-c", "if [ \"$NODE_ENV\" = production ]; then npm run build && node scripts/prod-server.mjs; else npm run dev; fi"]
