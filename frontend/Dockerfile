FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# NODE_ENV=production builds and serves the static/prerendered bundle
# (needed so Googlebot's raw HTML gets per-route canonical/title tags);
# anything else keeps the vite dev server with HMR for local development.
CMD ["sh", "-c", "if [ \"$NODE_ENV\" = production ]; then npm run build && npx serve dist -l 5173; else npm run dev; fi"]
