const SITE_NAME = 'MatchCalender'
const SITE_URL = 'https://matchcalender.com'
const DEFAULT_IMAGE = `${SITE_URL}/matchSync_bg.png`

function setMetaTag(attr: 'name' | 'property', key: string, content: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function setCanonical(path: string) {
  let el = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!el) {
    el = document.createElement('link')
    el.setAttribute('rel', 'canonical')
    document.head.appendChild(el)
  }
  el.setAttribute('href', `${SITE_URL}${path}`)
}

export function setJsonLd(id: string, data: unknown) {
  let el = document.getElementById(id) as HTMLScriptElement | null
  if (!el) {
    el = document.createElement('script')
    el.id = id
    el.type = 'application/ld+json'
    document.head.appendChild(el)
  }
  el.textContent = JSON.stringify(data)
}

export function removeJsonLd(id: string) {
  document.getElementById(id)?.remove()
}

export function applyPageMeta(opts: { title: string; description: string; path: string }) {
  const fullTitle = opts.title
  document.title = fullTitle

  setMetaTag('name', 'description', opts.description)
  setMetaTag('property', 'og:title', fullTitle)
  setMetaTag('property', 'og:description', opts.description)
  setMetaTag('property', 'og:type', 'website')
  setMetaTag('property', 'og:url', `${SITE_URL}${opts.path}`)
  setMetaTag('property', 'og:image', DEFAULT_IMAGE)
  setMetaTag('property', 'og:site_name', SITE_NAME)
  setMetaTag('name', 'twitter:card', 'summary_large_image')
  setMetaTag('name', 'twitter:title', fullTitle)
  setMetaTag('name', 'twitter:description', opts.description)
  setMetaTag('name', 'twitter:image', DEFAULT_IMAGE)
  setCanonical(opts.path)
}
