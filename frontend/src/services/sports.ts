import type { Sport, CalendarLink } from '@/types'
import { slugify } from '@/utils'

// ── Mode switch ───────────────────────────────────────────────────────────────
// When the backend is ready, set VITE_USE_API=true in .env and the service
// implementations below will hit the REST API instead of returning the
// hardcoded fallback data.
const USE_API = import.meta.env.VITE_USE_API === 'true'
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

// ── Hardcoded fallback data ───────────────────────────────────────────────────
const SPORTS: Sport[] = [
  { id: 'football', label: 'Football', icon: 'football', leagues: ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'MLS', 'Champions League'] },
  { id: 'hockey', label: 'Hockey', icon: 'hockey', leagues: ['NHL', 'AHL', 'KHL', 'SHL', 'NLA'] },
  { id: 'basketball', label: 'Basketball', icon: 'basketball', leagues: ['NBA', 'EuroLeague', 'NBL', 'WNBA'] },
  { id: 'baseball', label: 'Baseball', icon: 'baseball', leagues: ['MLB', 'NPB', 'KBO'] },
  { id: 'american-football', label: 'Am. Football', icon: 'amfootball', leagues: ['NFL', 'CFL', 'XFL'] },
  { id: 'rugby', label: 'Rugby', icon: 'rugby', leagues: ['Six Nations', 'Premiership Rugby', 'Top 14', 'Super Rugby'] },
]

const TEAMS: Record<string, string[]> = {
  'Premier League': ['Arsenal', 'Aston Villa', 'Brentford', 'Brighton', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Liverpool', 'Man City', 'Man United', 'Newcastle', 'Nottm Forest', 'Tottenham', 'West Ham', 'Wolves'],
  'La Liga': ['Atletico Madrid', 'Barcelona', 'Betis', 'Bilbao', 'Celta Vigo', 'Girona', 'Real Madrid', 'Sevilla', 'Sociedad', 'Valencia', 'Villarreal'],
  'Bundesliga': ['Bayern Munich', 'Borussia Dortmund', 'Leipzig', 'Bayer Leverkusen', 'Stuttgart', 'Frankfurt', 'Wolfsburg'],
  'NHL': ['Anaheim Ducks', 'Boston Bruins', 'Buffalo Sabres', 'Calgary Flames', 'Carolina Hurricanes', 'Chicago Blackhawks', 'Colorado Avalanche', 'Columbus Blue Jackets', 'Dallas Stars', 'Detroit Red Wings', 'Edmonton Oilers', 'Florida Panthers', 'Los Angeles Kings', 'Minnesota Wild', 'Montreal Canadiens', 'Nashville Predators', 'New Jersey Devils', 'New York Islanders', 'New York Rangers', 'Ottawa Senators', 'Philadelphia Flyers', 'Pittsburgh Penguins', 'San Jose Sharks', 'Seattle Kraken', 'St. Louis Blues', 'Tampa Bay Lightning', 'Toronto Maple Leafs', 'Utah Hockey Club', 'Vancouver Canucks', 'Vegas Golden Knights', 'Washington Capitals', 'Winnipeg Jets'],
  'NBA': ['Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets', 'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets', 'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers', 'LA Clippers', 'LA Lakers', 'Memphis Grizzlies', 'Miami Heat', 'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks', 'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns', 'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors', 'Utah Jazz', 'Washington Wizards'],
  'MLB': ['Arizona Diamondbacks', 'Atlanta Braves', 'Baltimore Orioles', 'Boston Red Sox', 'Chicago Cubs', 'Chicago White Sox', 'Cincinnati Reds', 'Cleveland Guardians', 'Colorado Rockies', 'Detroit Tigers', 'Houston Astros', 'Kansas City Royals', 'LA Angels', 'LA Dodgers', 'Miami Marlins', 'Milwaukee Brewers', 'Minnesota Twins', 'New York Mets', 'New York Yankees', 'Oakland Athletics', 'Philadelphia Phillies', 'Pittsburgh Pirates', 'San Diego Padres', 'San Francisco Giants', 'Seattle Mariners', 'St. Louis Cardinals', 'Tampa Bay Rays', 'Texas Rangers', 'Toronto Blue Jays', 'Washington Nationals'],
  'NFL': ['Arizona Cardinals', 'Atlanta Falcons', 'Baltimore Ravens', 'Buffalo Bills', 'Carolina Panthers', 'Chicago Bears', 'Cincinnati Bengals', 'Cleveland Browns', 'Dallas Cowboys', 'Denver Broncos', 'Detroit Lions', 'Green Bay Packers', 'Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars', 'Kansas City Chiefs', 'Las Vegas Raiders', 'LA Chargers', 'LA Rams', 'Miami Dolphins', 'Minnesota Vikings', 'New England Patriots', 'New Orleans Saints', 'New York Giants', 'New York Jets', 'Philadelphia Eagles', 'Pittsburgh Steelers', 'San Francisco 49ers', 'Seattle Seahawks', 'Tampa Bay Buccaneers', 'Tennessee Titans', 'Washington Commanders'],
}

function fallbackTeams(league: string): string[] {
  return TEAMS[league] ?? Array.from({ length: 8 }, (_, i) => `Team ${i + 1}`)
}

// ── Public service API ────────────────────────────────────────────────────────
export async function fetchSports(): Promise<Sport[]> {
  if (USE_API) {
    const res = await fetch(`${API_BASE}/sports`)
    if (!res.ok) throw new Error(`Failed to fetch sports: ${res.status}`)
    return res.json()
  }
  return SPORTS
}

export async function fetchTeams(league: string): Promise<string[]> {
  if (USE_API) {
    const res = await fetch(`${API_BASE}/leagues/${encodeURIComponent(slugify(league))}/teams`)
    if (!res.ok) throw new Error(`Failed to fetch teams: ${res.status}`)
    return res.json()
  }
  return fallbackTeams(league)
}

export async function fetchCalendarLink(team: string, league: string): Promise<CalendarLink> {
  if (USE_API) {
    const res = await fetch(`${API_BASE}/calendar?team=${encodeURIComponent(team)}&league=${encodeURIComponent(league)}`)
    if (!res.ok) throw new Error(`Failed to fetch calendar link: ${res.status}`)
    return res.json()
  }
  return {
    team,
    league,
    url: `webcal://cal.matchsync.io/v1/${slugify(league)}/${slugify(team)}.ics`,
  }
}
