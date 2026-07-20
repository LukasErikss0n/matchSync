// Best-effort visitor country guess used only to nudge which match/league gets
// featured on the hero card — no IP geolocation, no request to any server,
// nothing stored. Timezone is checked first since it reflects where the
// device actually is; navigator.language often just reflects OS/browser
// install language and can be wrong for the visitor's real location.
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
