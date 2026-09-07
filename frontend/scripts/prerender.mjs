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

// League pages are rendered client-side by MatchesView, so without this their
// static HTML is a title tag and an empty #app div — invisible to crawlers that
// don't run JS (GPTBot, PerplexityBot, ClaudeBot), and near-duplicate to the ones
// that only read <head>. Fixtures come from the same /api/matches the app uses.
// Both env vars are optional: with no API reachable at build time the pages still
// get their copy and internal links, just no fixture list.
// Defaults to the same API_TARGET/API_KEY prod-server.mjs proxies to, because the
// Dockerfile runs `npm run build` at container start with both already set and the
// backend already up — so production picks up fixtures with no compose change.
const API_TARGET = process.env.API_TARGET
const API_BASE = (
  process.env.PRERENDER_API_BASE ?? (API_TARGET ? `${API_TARGET}/api` : undefined)
)?.replace(/\/$/, '')
const API_KEY = process.env.PRERENDER_API_KEY ?? process.env.API_KEY

// Mirrors useLeagueEventsJsonLd.ts: same 25-fixture cap, same "still list a match
// that kicked off up to 3 days ago" window, so the static markup and the hydrated
// markup describe the same set.
const MAX_FIXTURES = 25
const STALE_WINDOW_MS = 3 * 86_400_000
const EVENT_DURATION_MS = {
  football: 2 * 60 * 60 * 1000,
  hockey: 2.5 * 60 * 60 * 1000,
  basketball: 2 * 60 * 60 * 1000,
  motorsport: 2 * 60 * 60 * 1000,
}
const DEFAULT_DURATION_MS = 2 * 60 * 60 * 1000

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
    league: p,
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

// Times are printed in UTC and labelled as such. The page itself renders kickoff
// in the visitor's own timezone once Vue mounts, but a static file has no timezone
// to detect, and an unlabelled time is the one thing worse than a converted one.
function formatKickoff(iso) {
  const d = new Date(iso)
  const date = d.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
  const time = d.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  })
  return `${date}, ${time} UTC`
}

function upcomingFixtures(fixtures) {
  const cutoff = Date.now() - STALE_WINDOW_MS
  return fixtures
    .filter((m) => new Date(m.start_time).getTime() >= cutoff)
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .slice(0, MAX_FIXTURES)
}

// Vue replaces this subtree on mount, so it is styling-irrelevant and content-critical,
// exactly like renderGuideBody above. What matters is that a crawler reading the raw
// file learns which league this page is for, in prose, with fixture names on it.
function renderLeagueBody(page, fixtures, siblings) {
  const rows = upcomingFixtures(fixtures)
    .map((m) => {
      const venue = m.venue ? ` — ${escapeHtml(m.venue)}` : ''
      return (
        `<li><time datetime="${escapeHtml(m.start_time)}">${escapeHtml(formatKickoff(m.start_time))}</time> ` +
        `${escapeHtml(m.home_team)} vs ${escapeHtml(m.away_team)}${venue}</li>`
      )
    })
    .join('')

  const fixtureSection = rows
    ? `<section><h2>Upcoming ${escapeHtml(page.name)} fixtures</h2><ul>${rows}</ul></section>`
    : ''

  const links = siblings
    .map((p) => `<li><a href="${p.path}">${escapeHtml(p.name)} calendar</a></li>`)
    .join('')

  return (
    `<main><h1>${escapeHtml(page.h1)}</h1><p>${escapeHtml(page.intro)}</p>` +
    `<p>${escapeHtml(page.description)}</p>` +
    fixtureSection +
    `<section><h2>How the ${escapeHtml(page.name)} calendar works</h2>` +
    `<p>Pick ${escapeHtml(page.name)} or a single team and MatchCalender gives you a webcal:// ` +
    `subscription link. Add it once in Google Calendar, Apple Calendar or Outlook and every ` +
    `fixture, kickoff change and playoff round arrives on its own. It is a live subscription, ` +
    `not a downloaded .ics file, so it never goes stale. Free, and no account needed.</p>` +
    `<p><a href="/guide">How to subscribe in Google, Apple and Outlook</a></p></section>` +
    `<section><h2>Other calendars</h2><ul>${links}</ul></section></main>`
  )
}

// Mirrors useLeagueEventsJsonLd.ts, including its id, so the composable updates this
// tag in place on mount instead of appending a second copy of the same ItemList.
function renderLeagueJsonLd(page, fixtures) {
  const events = upcomingFixtures(fixtures).filter((m) => !!m.venue)
  if (!events.length) return ''
  const data = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    itemListElement: events.map((m, i) => {
      const teams = [
        { '@type': 'SportsTeam', name: m.home_team },
        { '@type': 'SportsTeam', name: m.away_team },
      ]
      const start = new Date(m.start_time)
      const end = new Date(start.getTime() + (EVENT_DURATION_MS[m.sport] ?? DEFAULT_DURATION_MS))
      const crest = m.home_icon ?? m.away_icon
      return {
        '@type': 'ListItem',
        position: i + 1,
        item: {
          '@type': 'SportsEvent',
          name: `${m.home_team} vs ${m.away_team}`,
          description: `${page.name}: ${m.home_team} vs ${m.away_team} at ${m.venue} on ${start.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })}. Sync the fixture to your calendar with MatchCalender.`,
          startDate: m.start_time,
          endDate: end.toISOString(),
          eventStatus: 'https://schema.org/EventScheduled',
          eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
          image: crest && /^https?:\/\//.test(crest) ? crest : `${SITE_URL}/logo-social.png`,
          location: { '@type': 'Place', name: m.venue },
          competitor: teams,
          performer: teams,
          organizer: { '@type': 'Organization', name: page.name, url: `${SITE_URL}${page.path}` },
        },
      }
    }),
  }
  return `<script type="application/ld+json" id="league-events-jsonld">${JSON.stringify(data)}<\/script>`
}

// A build without API access is a normal case (CI, a local dist rebuild), so a failed
// fetch degrades to a fixture-less page rather than failing the build. Missing meta
// tags throw below because those are a code bug; an unreachable API is not.
async function fetchLeagueFixtures(slug) {
  if (!API_BASE) return []
  const url = `${API_BASE}/matches?league=${encodeURIComponent(slug)}&limit=200`
  try {
    const res = await fetch(url, {
      headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
      signal: AbortSignal.timeout(15_000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch (err) {
    console.warn(`prerender: no fixtures for ${slug} (${err.message}), rendering copy only.`)
    return []
  }
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

function injectBody(html, body, routePath) {
  if (!html.includes('<div id="app"></div>')) {
    throw new Error(
      `prerender: could not find the empty #app div to inject ${routePath} content into.`,
    )
  }
  return html.replace('<div id="app"></div>', `<div id="app">${body}</div>`)
}

const baseHtml = await readFile(path.join(distDir, 'index.html'), 'utf-8')

// One request per league, in parallel, before the write loop — 14 sequential
// round trips is the difference between a build step and a coffee break.
const fixturesByLeague = new Map(
  await Promise.all(
    leaguePages.map(async (p) => [p.slug, await fetchLeagueFixtures(p.slug)]),
  ),
)
if (!API_BASE) {
  console.warn(
    'prerender: no PRERENDER_API_BASE or API_TARGET, league pages get copy but no fixtures.',
  )
}

for (const route of routes) {
  let html = applyRouteMeta(baseHtml, route)
  if (route.league) {
    const fixtures = fixturesByLeague.get(route.league.slug) ?? []
    const siblings = leaguePages.filter((p) => p.path !== route.league.path)
    html = injectBody(html, renderLeagueBody(route.league, fixtures, siblings), route.path)
    const jsonLd = renderLeagueJsonLd(route.league, fixtures)
    if (jsonLd) html = html.replace('</head>', `${jsonLd}</head>`)
  }
  if (route.guide) {
    html = injectBody(html, renderGuideBody(route.guide), route.path)
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
