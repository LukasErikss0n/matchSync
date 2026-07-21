// Production server: serves the built+prerendered dist/ and proxies /api/*
// to the backend, mirroring vite.config.ts's dev-only proxy (including
// attaching X-API-Key server-side so the key never reaches the browser).
// `npx serve dist` alone can't do the proxy half, which is why /api calls
// 404 once NODE_ENV=production switches the Dockerfile off the vite dev server.
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const distDir = path.join(__dirname, '..', 'dist')
const PORT = process.env.PORT ? Number(process.env.PORT) : 5173
const API_TARGET = process.env.API_TARGET ?? 'http://localhost:8000'
const API_KEY = process.env.API_KEY

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
}

function contentType(filePath) {
  return MIME_TYPES[path.extname(filePath)] ?? 'application/octet-stream'
}

// Prerender.mjs writes one index.html per route (e.g. dist/premier-league/index.html)
// so Googlebot's raw fetch sees the right per-page meta tags — resolve those first,
// and only fall back to the root SPA shell for paths we didn't prerender.
function resolveStaticFile(urlPath) {
  const clean = urlPath.split('?')[0].split('#')[0]
  const candidates =
    clean === '/'
      ? [path.join(distDir, 'index.html')]
      : [
          path.join(distDir, clean),
          path.join(distDir, clean, 'index.html'),
          path.join(distDir, `${clean}.html`),
        ]
  for (const candidate of candidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      return candidate
    }
  }
  const hasExtension = path.extname(clean) !== ''
  return hasExtension ? null : path.join(distDir, 'index.html')
}

function serveStatic(req, res) {
  const filePath = resolveStaticFile(req.url ?? '/')
  if (!filePath) {
    res.writeHead(404)
    res.end('Not found')
    return
  }
  res.writeHead(200, { 'Content-Type': contentType(filePath) })
  fs.createReadStream(filePath).pipe(res)
}

function proxyApi(req, res) {
  const target = new URL(req.url ?? '/', API_TARGET)
  const headers = { ...req.headers, host: target.host }
  if (API_KEY) headers['x-api-key'] = API_KEY

  const proxyReq = http.request(target, { method: req.method, headers }, (proxyRes) => {
    res.writeHead(proxyRes.statusCode ?? 502, proxyRes.headers)
    proxyRes.pipe(res)
  })
  proxyReq.on('error', (err) => {
    console.error('API proxy error:', err.message)
    res.writeHead(502)
    res.end('Bad gateway')
  })
  req.pipe(proxyReq)
}

const server = http.createServer((req, res) => {
  if (req.url?.startsWith('/api')) {
    proxyApi(req, res)
  } else {
    serveStatic(req, res)
  }
})

server.listen(PORT, () => {
  console.log(`Production server listening on http://0.0.0.0:${PORT}`)
  console.log(`Proxying /api -> ${API_TARGET}`)
})
