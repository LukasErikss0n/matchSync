/**
 * Deterministic visual identity for a club, derived from its name alone.
 *
 * There is no club-colour data in the DB (teams only carry a crest URL), so
 * the hero's duotone panel synthesises one: a stable full-saturation "club
 * colour" used for the crest, plus an "ink" colour guaranteed to be legible
 * on top of it. The same colour at low alpha becomes that club's half of the
 * panel wash, which is why the palette is tuned to read well both at full
 * strength on dark navy and at ~16% over it.
 */

// Full-saturation crest colours. Every entry is bright enough to stay clearly
// lighter than its own 16% wash (the wash must never become the surface).
const PALETTE = [
  '#5b9bd5', // sky blue
  '#e0596b', // red
  '#4169c9', // royal blue
  '#e9a13b', // amber
  '#33b189', // green
  '#8b6fd6', // violet
  '#d45c96', // magenta
  '#2f4b8c', // navy
  '#38a3bd', // teal
  '#c98b2a', // gold
  '#c2455b', // crimson
  '#5f7a99', // slate
]

// Club-type abbreviations that carry no identity on their own — dropped before
// building a monogram so "IF Elfsborg" reads as ELF rather than IFE.
const GENERIC_TOKENS = new Set([
  'FC', 'FK', 'SK', 'BK', 'IF', 'IK', 'IFK', 'CF', 'AFC', 'FF', 'SC', 'AC',
  'HC', 'HF', 'HK', 'BOIS', 'SV', 'CD', 'RC', 'US', 'SS', 'AS',
])

function hashOf(name: string): number {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  return hash
}

/**
 * A 3-letter monogram. Football's real 3-letter codes are inconsistent enough
 * that no rule reproduces all of them; this favours being stable, unique and
 * pronounceable over matching any particular league's official abbreviations.
 */
export function monogramOf(name: string): string {
  // Hyphens separate name parts just like spaces do, so Paris Saint-Germain
  // yields PSG rather than treating "Saint-Germain" as one word.
  const raw = name.trim().split(/[\s-]+/).filter(Boolean)
  if (raw.length === 0) return '?'

  // An existing all-caps 3-letter token IS the club's identity (AIK, PSG).
  const acronym = raw.find((w) => w.length === 3 && w === w.toUpperCase() && /^[A-ZÅÄÖ]+$/.test(w))
  if (acronym) return acronym

  const words = raw.filter((w) => !GENERIC_TOKENS.has(w.toUpperCase()))
  const parts = words.length > 0 ? words : raw

  if (parts.length === 1) return parts[0].slice(0, 3).toUpperCase()
  // Two words: one letter from the first, two from the second — this is what
  // yields the familiar MUN / MCI shape rather than an ambiguous MAN / MAN.
  if (parts.length === 2) {
    return (parts[0][0] + parts[1].slice(0, 2)).toUpperCase()
  }
  return parts.slice(0, 3).map((w) => w[0]).join('').toUpperCase()
}

/** Relative luminance (sRGB, WCAG) of a #rrggbb colour. */
function luminance(hex: string): number {
  const channel = (v: number) => {
    const c = v / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  const r = channel(parseInt(hex.slice(1, 3), 16))
  const g = channel(parseInt(hex.slice(3, 5), 16))
  const b = channel(parseInt(hex.slice(5, 7), 16))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

export interface ClubIdentity {
  monogram: string
  /** Full-saturation crest fill. */
  color: string
  /** Monogram colour, chosen for contrast against `color`. */
  ink: string
}

export function clubIdentity(
  name: string,
  opts: { color?: string | null; avoid?: string } = {},
): ClubIdentity {
  // The real crest colour, extracted server-side, is always preferred; the
  // palette is the fallback for teams whose crest yielded nothing usable
  // (or that have no crest at all).
  let color = opts.color ?? null
  if (!color) {
    let index = hashOf(name) % PALETTE.length
    // The two halves of the panel have to stay distinguishable, so an away
    // club that hashes onto the home club's colour is nudged to another entry.
    if (opts.avoid && PALETTE[index] === opts.avoid) index = (index + 5) % PALETTE.length
    color = PALETTE[index]
  }
  return {
    monogram: monogramOf(name),
    color,
    ink: luminance(color) > 0.42 ? '#0b1626' : '#f4f7fb',
  }
}
