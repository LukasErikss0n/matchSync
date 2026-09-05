const PALETTE = [
  '#5b9bd5',
  '#e0596b',
  '#4169c9',
  '#e9a13b',
  '#33b189',
  '#8b6fd6',
  '#d45c96',
  '#2f4b8c',
  '#38a3bd',
  '#c98b2a',
  '#c2455b',
  '#5f7a99',
]

const GENERIC_CLUB_ABBREVIATIONS = new Set([
  'FC', 'FK', 'SK', 'BK', 'IF', 'IK', 'IFK', 'CF', 'AFC', 'FF', 'SC', 'AC',
  'HC', 'HF', 'HK', 'BOIS', 'SV', 'CD', 'RC', 'US', 'SS', 'AS',
])

function hashOf(name: string): number {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  return hash
}

export function monogramOf(name: string): string {
  const nameParts = name.trim().split(/[\s-]+/).filter(Boolean)
  if (nameParts.length === 0) return '?'

  const existingAcronym = nameParts.find(
    (w) => w.length === 3 && w === w.toUpperCase() && /^[A-ZÅÄÖ]+$/.test(w),
  )
  if (existingAcronym) return existingAcronym

  const meaningfulParts = nameParts.filter((w) => !GENERIC_CLUB_ABBREVIATIONS.has(w.toUpperCase()))
  const parts = meaningfulParts.length > 0 ? meaningfulParts : nameParts

  if (parts.length === 1) return parts[0].slice(0, 3).toUpperCase()
  if (parts.length === 2) {
    return (parts[0][0] + parts[1].slice(0, 2)).toUpperCase()
  }
  return parts.slice(0, 3).map((w) => w[0]).join('').toUpperCase()
}

function relativeLuminance(hex: string): number {
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
  color: string
  ink: string
}

export function clubIdentity(
  name: string,
  opts: { avoid?: string } = {},
): ClubIdentity {
  let index = hashOf(name) % PALETTE.length
  if (opts.avoid && PALETTE[index] === opts.avoid) index = (index + 5) % PALETTE.length
  const color = PALETTE[index]
  return {
    monogram: monogramOf(name),
    color,
    ink: relativeLuminance(color) > 0.42 ? '#0b1626' : '#f4f7fb',
  }
}
