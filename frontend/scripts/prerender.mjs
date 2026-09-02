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
  {
    path: '/support',
    title: 'Report a problem | MatchCalender',
    description:
      'Report a bug, suggest an improvement, or ask a question about MatchCalender.',
  },
  ...leaguePages.map((p) => ({
    path: p.path,
    title: p.title,
    description: p.description,
  })),
]

// Vite leaves index.html's multi-line <meta> tags (description, og:description,
// twitter:description) formatted across several lines, so a pattern written with
// literal single spaces silently matches nothing and every route inherits the
// homepage copy. Every gap here is \\s+ for that reason, and each replacement is
// asserted below so a future reformat fails the build instead of shipping
// 20 pages with one description.
function metaPattern(attr, name) {
  return new RegExp(`<meta\\s+${attr}="${name}"\\s+content="[^"]*"\\s*/?>`, 'i')
}

function applyRouteMeta(html, route) {
  const url = `${SITE_URL}${route.path}`
  const edits = [
    ['title', /<title>.*?<\/title>/s, `<title>${route.title}</title>`],
    [
      'canonical',
      /<link\s+rel="canonical"\s+href="[^"]*"\s*\/?>/i,
      `<link rel="canonical" href="${url}" />`,
    ],
    [
      'description',
      metaPattern('name', 'description'),
      `<meta name="description" content="${route.description}" />`,
    ],
    ['og:url', metaPattern('property', 'og:url'), `<meta property="og:url" content="${url}" />`],
    [
      'og:title',
      metaPattern('property', 'og:title'),
      `<meta property="og:title" content="${route.title}" />`,
    ],
    [
      'og:description',
      metaPattern('property', 'og:description'),
      `<meta property="og:description" content="${route.description}" />`,
    ],
    [
      'twitter:title',
      metaPattern('name', 'twitter:title'),
      `<meta name="twitter:title" content="${route.title}" />`,
    ],
    [
      'twitter:description',
      metaPattern('name', 'twitter:description'),
      `<meta name="twitter:description" content="${route.description}" />`,
    ],
  ]

  let out = html
  for (const [label, pattern, replacement] of edits) {
    if (!pattern.test(out)) {
      throw new Error(
        `prerender: no <${label}> tag matched in index.html for ${route.path}. ` +
          `The tag was probably reformatted, fix the pattern rather than shipping duplicate meta.`,
      )
    }
    out = out.replace(pattern, replacement)
  }
  return out
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
