// Generates a static index.html per route in dist/, each with the correct
// title/canonical/description baked in, so Googlebot's raw HTML fetch already
// matches what the client-side router would render — no more homepage
// canonical being applied to every route.
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const distDir = path.join(__dirname, '..', 'dist')
const SITE_URL = 'https://matchcalender.com'

// Single source of truth for the per-league landing pages (also drives the
// router and sitemap). Read as JSON so this plain-Node script needs no build.
const leaguePages = JSON.parse(
  await readFile(path.join(__dirname, '..', 'src', 'data', 'leaguePages.json'), 'utf-8'),
)

const HOME_DESCRIPTION =
  'Subscribe once and get every fixture, reschedule and playoff round auto-synced to your calendar for football, hockey, basketball and more.'

const routes = [
  {
    path: '/',
    title: 'MatchCalender, live sports calendars that stay in sync',
    description: HOME_DESCRIPTION,
  },
  {
    path: '/matches',
    title: 'All matches, fixtures & Results | MatchCalender',
    description:
      'Browse every fixture and result by league or team, updated live and ready to sync to your calendar.',
  },
  {
    path: '/api-docs',
    title: 'API docs | MatchCalender',
    description:
      'Every calendar link generated on MatchCalender is a standard iCal feed you can subscribe to from any calendar app, see the feed URL format and parameters.',
  },
  {
    path: '/privacy',
    title: 'Privacy policy | MatchCalender',
    description:
      'MatchCalender only stores the sport, team and league selections needed to generate your calendar link, no accounts, no tracking, no ads.',
  },
  {
    path: '/terms',
    title: 'Terms of service | MatchCalender',
    description:
      'Read the terms covering personal use of MatchCalender, including sharing calendar links with friends and the restriction on commercial redistribution.',
  },
  ...leaguePages.map((p) => ({
    path: p.path,
    title: p.title,
    description: p.description,
  })),
]

function applyRouteMeta(html, route) {
  const url = `${SITE_URL}${route.path}`
  return html
    .replace(/<title>.*?<\/title>/s, `<title>${route.title}</title>`)
    .replace(/<link rel="canonical" href="[^"]*"\s*\/?>/, `<link rel="canonical" href="${url}" />`)
    .replace(/<meta name="description" content="[^"]*"\s*\/?>/, `<meta name="description" content="${route.description}" />`)
    .replace(/<meta property="og:url" content="[^"]*"\s*\/?>/, `<meta property="og:url" content="${url}" />`)
    .replace(/<meta property="og:title" content="[^"]*"\s*\/?>/, `<meta property="og:title" content="${route.title}" />`)
    .replace(/<meta property="og:description" content="[^"]*"\s*\/?>/, `<meta property="og:description" content="${route.description}" />`)
    .replace(/<meta name="twitter:title" content="[^"]*"\s*\/?>/, `<meta name="twitter:title" content="${route.title}" />`)
    .replace(/<meta name="twitter:description" content="[^"]*"\s*\/?>/, `<meta name="twitter:description" content="${route.description}" />`)
}

const baseHtml = await readFile(path.join(distDir, 'index.html'), 'utf-8')

for (const route of routes) {
  const html = applyRouteMeta(baseHtml, route)
  if (route.path === '/') {
    await writeFile(path.join(distDir, 'index.html'), html)
    continue
  }
  const dir = path.join(distDir, route.path)
  await mkdir(dir, { recursive: true })
  await writeFile(path.join(dir, 'index.html'), html)
}

console.log(`Prerendered ${routes.length} routes.`)
