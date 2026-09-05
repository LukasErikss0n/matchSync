const TIMEZONE_COUNTRY: Record<string, string> = {
  'Europe/Stockholm': 'SE',
  'Europe/London': 'GB',
  'Europe/Belfast': 'GB',
  'Europe/Helsinki': 'FI',
  'Europe/Oslo': 'NO',
  'Europe/Copenhagen': 'DK',
}

export function detectRegion(): string | undefined {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
    const fromTz = TIMEZONE_COUNTRY[tz]
    if (fromTz) return fromTz
  } catch {
    // Intl/timezone lookup unsupported — fall through to locale.
  }

  try {
    const region = new Intl.Locale(navigator.language).maximize().region
    if (region) return region
  } catch {
    // Unparseable locale — nothing more we can do.
  }

  return undefined
}
