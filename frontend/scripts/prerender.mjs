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

// The guide pages are the only routes whose body HTML is prerendered. They exist
// to be read by AI crawlers (GPTBot, PerplexityBot, ClaudeBot), which unlike
// Googlebot do not execute JavaScript — a client-rendered answer is invisible to
// them, so the copy has to be in the static file.
const guidePages = JSON.parse(
  await readFile(path.join(__dirname, '..', 'src', 'data', 'guidePages.json'), 'utf-8'),
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
  ...Object.values(guidePages).map((g) => ({
    path: g.path,
    title: g.title,
    description: g.description,
    guide: g,
  })),
]

const escapeHtml = (value) =>
  String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// Mirrors GuideView.vue's markup closely enough that the crawler-visible copy and
// the hydrated copy say the same thing. It does not need to match class-for-class:
// Vue replaces this subtree on mount, so it is styling-irrelevant and content-critical.
function renderGuideBody(guide) {
  const sections = guide.sections
    .map((section) => {
      const paragraphs = section.a.map((p) => `<p>${escapeHtml(p)}</p>`).join('')
      const steps = section.steps
        ? `<ol>${section.steps.map((step) => `<li>${escapeHtml(step)}</li>`).join('')}</ol>`
        : ''
      return `<section id="${escapeHtml(section.id)}"><h2>${escapeHtml(section.q)}</h2>${paragraphs}${steps}</section>`
    })
    .join('')

  const toc = guide.sections
    .map((section) => `<li><a href="#${escapeHtml(section.id)}">${escapeHtml(section.q)}</a></li>`)
    .join('')

  return (
    `<main><h1>${escapeHtml(guide.h1)}</h1><p>${escapeHtml(guide.intro)}</p>` +
    `<nav><ul>${toc}</ul></nav>${sections}</main>`
  )
}

// FAQPage, because every section is literally a question with a self-contained
// answer — the shape AI engines and rich results both extract from.
function renderGuideJsonLd(guide) {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    inLanguage: guide.lang,
    url: `${SITE_URL}${guide.path}`,
    name: guide.h1,
    description: guide.description,
    mainEntity: guide.sections.map((section) => ({
      '@type': 'Question',
      name: section.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: [...section.a, ...(section.steps ?? [])].join(' '),
      },
    })),
  }
  return `<script type="application/ld+json">${JSON.stringify(data)}<\/script>`
}

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
  let html = applyRouteMeta(baseHtml, route)
  if (route.guide) {
    const body = renderGuideBody(route.guide)
    if (!html.includes('<div id="app"></div>')) {
      throw new Error('prerender: could not find the empty #app div to inject guide content into.')
    }
    html = html
      .replace('<div id="app"></div>', `<div id="app">${body}</div>`)
      .replace(/<html lang="[^"]*"/, `<html lang="${route.guide.lang}"`)
      .replace('</head>', `${renderGuideJsonLd(route.guide)}</head>`)
  }
  if (route.path === '/') {
    await writeFile(path.join(distDir, 'index.html'), html)
    continue
  }
  const dir = path.join(distDir, route.path)
  await mkdir(dir, { recursive: true })
  await writeFile(path.join(dir, 'index.html'), html)
}

console.log(`Prerendered ${routes.length} routes.`)
