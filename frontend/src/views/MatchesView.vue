<template>
    <Navbar @get-started="openSportModal" />

    <main class="min-h-screen">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
            <!-- Header -->
            <p class="section-label mb-2">Fixtures &amp; Results</p>
            <h1
                class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2"
                style="letter-spacing: -0.02em"
            >
                All matches
            </h1>
            <p class="mb-2 max-w-xl" style="color: var(--ms-muted)">
                Browse every fixture by league or team.
            </p>
            <div
                v-if="lastUpdatedText"
                class="inline-flex items-center gap-1.5 mb-7 text-xs font-semibold"
                style="color: rgba(244, 247, 251, 0.45)"
            >
                <span class="live-dot" />
                Updated {{ lastUpdatedText }}
            </div>

            <!-- Filters -->
            <div class="flex flex-wrap items-center gap-2.5 mb-8">
                <!-- League -->
                <div class="relative">
                    <button
                        class="filter-pill active"
                        @click="toggle('league')"
                    >
                        {{ selectedLeague?.name ?? "League" }}
                        <ChevronDown />
                    </button>
                    <div v-if="open === 'league'" class="filter-menu">
                        <button
                            v-for="opt in leagueOptions"
                            :key="`${opt.sport}:${opt.slug}`"
                            class="filter-item"
                            :class="{
                                chosen:
                                    selectedLeague?.sport === opt.sport &&
                                    selectedLeague?.slug === opt.slug,
                            }"
                            @click="selectLeague(opt)"
                        >
                            {{ opt.name }}
                            <span class="text-xs ml-2" style="color: rgba(244,247,251,.4)">{{
                                opt.sportLabel
                            }}</span>
                        </button>
                    </div>
                </div>

                <!-- Season (informational) -->
                <span class="filter-pill cursor-default">{{
                    season
                }}</span>

                <!-- Team -->
                <div class="relative">
                    <button
                        class="filter-pill"
                        :class="{ active: !!selectedTeamSlug }"
                        @click="toggle('team')"
                    >
                        {{ selectedTeamName }}
                        <ChevronDown />
                    </button>
                    <div
                        v-if="open === 'team'"
                        class="filter-menu right-align max-h-72 overflow-y-auto"
                    >
                        <button
                            class="filter-item"
                            :class="{ chosen: !selectedTeamSlug }"
                            @click="selectTeam(null)"
                        >
                            All teams
                        </button>
                        <button
                            v-for="t in teamOptions"
                            :key="t.slug"
                            class="filter-item"
                            :class="{ chosen: selectedTeamSlug === t.slug }"
                            @click="selectTeam(t.slug)"
                        >
                            <TeamBadge
                                :name="t.name"
                                :icon="t.icon"
                                :size="22"
                            />
                            {{ t.name }}
                        </button>
                    </div>
                </div>

                <button
                    v-if="selectedTeamSlug || weekOffset !== 0"
                    class="filter-pill flex items-center gap-1.5"
                    @click="resetFilters"
                >
                    <Icon name="refresh" class="!w-3.5 !h-3.5" /> Reset
                </button>
            </div>

            <!-- Click-away backdrop for dropdowns -->
            <div v-if="open" class="fixed inset-0 z-10" @click="open = null" />

            <!-- Week pager -->
            <div class="flex items-center justify-center gap-5 mb-6">
                <button
                    class="pager-btn"
                    aria-label="Previous week"
                    @click="weekOffset--"
                >
                    <ChevronDown class="rotate-90" />
                </button>
                <div class="text-center">
                    <div class="font-extrabold">
                        {{ windowTitle }}
                    </div>
                    <div class="text-xs mt-0.5" style="color: rgba(244,247,251,.45)">
                        {{ windowSubtitle }}
                    </div>
                </div>
                <button
                    class="pager-btn"
                    aria-label="Next week"
                    @click="weekOffset++"
                >
                    <ChevronDown class="-rotate-90" />
                </button>
            </div>

            <!-- Loading -->
            <div
                v-if="loading"
                class="text-center py-16 text-sm"
                style="color: var(--ms-muted)"
            >
                Loading matches…
            </div>

            <!-- Match groups -->
            <template v-else-if="visibleGroups.length">
                <div
                    v-for="group in visibleGroups"
                    :key="group.key"
                    class="glass-card rounded-[24px] overflow-hidden mb-3.5"
                >
                    <div
                        class="flex items-center justify-between px-4 sm:px-6 py-3.5 bg-white/[0.05] border-b border-white/[0.08]"
                    >
                        <span class="font-extrabold text-sm">{{
                            group.label
                        }}</span>
                        <span class="text-xs font-semibold" style="color: rgba(244,247,251,.45)"
                            >{{ group.matches.length }}
                            {{
                                group.matches.length === 1 ? "match" : "matches"
                            }}</span
                        >
                    </div>
                    <div>
                        <MatchRow
                            v-for="m in group.matches"
                            :key="m.id"
                            :match="m"
                            @add="onAddToCalendar"
                        />
                    </div>
                </div>
            </template>

            <!-- Empty -->
            <div v-else class="text-center py-16">
                <p class="font-semibold">No matches this week</p>
            </div>

            <!-- Footer CTA -->
            <div
                v-if="selectedLeague"
                class="mt-8 glass-card rounded-2xl px-5 py-4 flex items-center justify-between gap-4"
            >
                <div class="flex items-center gap-3 min-w-0">
                    <div class="flex-shrink-0 w-9 h-9 rounded-xl feature-icon flex items-center justify-center">
                        <Icon name="calendar" class="!w-4 !h-4" />
                    </div>
                    <div class="min-w-0">
                        <p class="font-bold text-sm truncate">{{ selectedLeague.name }} calendar</p>
                        <p class="text-xs" style="color: rgba(244,247,251,.45)">Subscribe once, stay synced forever</p>
                    </div>
                </div>
                <button
                    class="flex-shrink-0 flex items-center gap-2 ms-btn-primary rounded-full font-bold px-4 py-2.5 text-sm whitespace-nowrap"
                    @click="openSportModal"
                >
                    <Icon name="link" class="!w-3.5 !h-3.5" />
                    Get link
                </button>
            </div>

            <!-- Season FAQ (built from the live fixture list — helps long-tail search) -->
            <div v-if="seasonFaq" class="mt-6 glass-card rounded-2xl px-5 py-5">
                <p class="section-label mb-3">FAQ</p>
                <div v-for="item in seasonFaq.items" :key="item.question" class="mb-4 last:mb-0">
                    <p class="font-bold text-sm mb-1">{{ item.question }}</p>
                    <p class="text-sm" style="color: var(--ms-muted)">{{ item.answer }}</p>
                </div>
            </div>
        </div>
    </main>

    <TeamSelectorModal
        v-if="showModal"
        :initial-sport="modalSport"
        :initial-team="modalTeam"
        @close="closeModal"
    />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { League, Match, SeasonStats, Sport, Team } from "@/types";
import {
    fetchSports,
    fetchTeams,
    fetchTeam,
    fetchMatches,
    fetchLastUpdated,
    fetchSeasonStats,
} from "@/services/sports";
import { cachedFeaturedMatch, refreshFeaturedMatch } from "@/services/featuredMatchCache";
import { setJsonLd, removeJsonLd } from "@/utils/seo";
import Navbar from "@/components/Navbar.vue";
import Icon from "@/components/Icon.vue";
import TeamBadge from "@/components/TeamBadge.vue";
import MatchRow from "@/components/MatchRow.vue";
import TeamSelectorModal from "@/components/TeamSelectorModal.vue";

// Tiny inline chevron so we don't have to extend the Icon registry
const ChevronDown = (
    _: unknown,
    { attrs }: { attrs: Record<string, unknown> },
) => {
    const { class: cls, ...rest } = attrs;
    return h(
        "svg",
        {
            viewBox: "0 0 24 24",
            fill: "none",
            stroke: "currentColor",
            "stroke-width": 2.2,
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            class: ["w-3.5 h-3.5", cls],
            ...rest,
        },
        [h("polyline", { points: "6 9 12 15 18 9" })],
    );
};

type LeagueOption = League & { sport: string; sportLabel: string };

const route = useRoute();
const router = useRouter();

const sports = ref<Sport[]>([]);
const selectedLeague = ref<LeagueOption | null>(null);
const teamOptions = ref<Team[]>([]);
const selectedTeamSlug = ref<string | null>(null);
const matches = ref<Match[]>([]);
const loading = ref(false);
const open = ref<"league" | "team" | null>(null);
const weekOffset = ref(0);

// Modal state (reuses the home subscribe flow)
const showModal = ref(false);
const modalSport = ref<string | null>(null);
const modalTeam = ref<Team | null>(null);

// "Updated X ago" badge — reflects the fetcher's last successful run, not page load
const lastUpdatedAt = ref<Date | null>(null);
const now = ref(Date.now());
let clockTimer: number | null = null;

const lastUpdatedText = computed(() => {
    if (!lastUpdatedAt.value) return null;
    const diffSec = Math.max(0, Math.floor((now.value - lastUpdatedAt.value.getTime()) / 1000));
    if (diffSec < 60) return "just now";
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? "" : "s"} ago`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? "" : "s"} ago`;
    const diffDay = Math.floor(diffHour / 24);
    return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`;
});

const leagueOptions = computed<LeagueOption[]>(() =>
    sports.value.flatMap((s) =>
        s.leagues.map((l) => ({ ...l, sport: s.id, sportLabel: s.label })),
    ),
);

const selectedTeamName = computed(() => {
    if (!selectedTeamSlug.value) return "All teams";
    return (
        teamOptions.value.find((t) => t.slug === selectedTeamSlug.value)
            ?.name ?? "All teams"
    );
});

// Per-league season config.
// threshold: 0-indexed month. atStart=true → flip AT that month (season start);
//            atStart=false → flip AFTER that month (season end).
// singleYear: true → show "2026"; false → show "2025/26".
type SeasonCfg = { threshold: number; atStart: boolean; singleYear: boolean };
const LEAGUE_SEASON: Record<string, SeasonCfg> = {
    "premier-league": { threshold: 4, atStart: false, singleYear: false }, // after May
    "uefa-champions-league": {
        threshold: 4,
        atStart: false,
        singleYear: false,
    }, // after May
    "uefa-conference-league": {
        threshold: 4,
        atStart: false,
        singleYear: false,
    },
    "fa-cup": { threshold: 4, atStart: false, singleYear: false },
    "efl-cup": { threshold: 2, atStart: false, singleYear: false }, // after March
    "uefa-europa-league": { threshold: 4, atStart: false, singleYear: false },
    allsvenskan: { threshold: 3, atStart: true, singleYear: true }, // at April, single year
    shl: { threshold: 2, atStart: false, singleYear: false }, // after March
    sdhl: { threshold: 2, atStart: false, singleYear: false },
    "sbl-herrar": { threshold: 3, atStart: false, singleYear: false }, // after April (finals end early May)
    "sbl-damer": { threshold: 3, atStart: false, singleYear: false },
    "iihf-world-championship": {
        threshold: 4,
        atStart: false,
        singleYear: false,
    },
};

const season = computed(() => {
    // Based on the week currently being browsed, not today's date — otherwise
    // paging into a past/future week shows a season label that doesn't match
    // the matches actually on screen.
    const viewed = windowStart.value;
    const m = viewed.getMonth();
    const y = viewed.getFullYear();
    const cfg = LEAGUE_SEASON[selectedLeague.value?.slug ?? ""];
    const start = cfg
        ? cfg.atStart
            ? m >= cfg.threshold
                ? y
                : y - 1
            : m > cfg.threshold
              ? y
              : y - 1
        : m > 4
          ? y
          : y - 1;
    return cfg?.singleYear
        ? `${start}`
        : `${start}/${String((start + 1) % 100).padStart(2, "0")}`;
});

function toggle(which: "league" | "team") {
    open.value = open.value === which ? null : which;
}

function pushQuery(league: LeagueOption | null, team: string | null) {
    router.replace({
        query: {
            league: league?.slug ?? undefined,
            filter: team ?? undefined,
        },
    });
}

async function selectLeague(opt: LeagueOption) {
    open.value = null;
    if (
        selectedLeague.value?.sport === opt.sport &&
        selectedLeague.value?.slug === opt.slug
    )
        return;
    selectedLeague.value = opt;
    selectedTeamSlug.value = null;
    pushQuery(opt, null);
    await Promise.all([loadTeams(), loadMatches(), loadSeasonStats()]);
}

function selectTeam(slug: string | null) {
    open.value = null;
    selectedTeamSlug.value = slug;
    pushQuery(selectedLeague.value, slug);
    loadMatches();
}

function resetFilters() {
    selectedTeamSlug.value = null;
    weekOffset.value = 0;
    pushQuery(selectedLeague.value, null);
    loadMatches();
}

async function loadTeams() {
    if (!selectedLeague.value) return;
    const all = await fetchTeams({
        sport: selectedLeague.value.sport,
        limit: 200,
    });
    teamOptions.value = all
        .filter((t) =>
            t.leagues.some((l) => l.slug === selectedLeague.value!.slug),
        )
        .sort((a, b) => a.name.localeCompare(b.name));
}

const seasonStats = ref<SeasonStats | null>(null);

async function loadSeasonStats() {
    if (!selectedLeague.value) return;
    seasonStats.value = null;
    try {
        seasonStats.value = await fetchSeasonStats(selectedLeague.value.slug);
    } catch {
        /* FAQ just won't show for this league */
    }
}

async function loadMatches() {
    if (!selectedLeague.value) return;
    loading.value = true;
    try {
        matches.value = await fetchMatches({
            sport: selectedLeague.value.sport,
            league: selectedLeague.value.slug,
            team: selectedTeamSlug.value ?? undefined,
        });
        jumpToRelevantWeek();
    } finally {
        loading.value = false;
    }
}

// ── Week windowing ───────────────────────────────────────────────────────────
const DAY = 86_400_000;

function startOfWeek(d: Date): Date {
    const x = new Date(d);
    x.setHours(0, 0, 0, 0);
    const day = (x.getDay() + 6) % 7; // Mon = 0
    x.setDate(x.getDate() - day);
    return x;
}

const windowStart = computed(() => {
    const base = startOfWeek(new Date());
    return new Date(base.getTime() + weekOffset.value * 7 * DAY);
});
const windowEnd = computed(
    () => new Date(windowStart.value.getTime() + 7 * DAY),
);

// Snap the pager to the week holding the next upcoming match (else the latest one)
function jumpToRelevantWeek() {
    if (!matches.value.length) {
        weekOffset.value = 0;
        return;
    }
    const now = Date.now();
    const sorted = [...matches.value].sort(
        (a, b) =>
            new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
    );
    const target =
        sorted.find((m) => new Date(m.start_time).getTime() >= now) ??
        sorted[sorted.length - 1];
    const base = startOfWeek(new Date()).getTime();
    const tgt = startOfWeek(new Date(target.start_time)).getTime();
    weekOffset.value = Math.round((tgt - base) / (7 * DAY));
}

const visibleMatches = computed(() =>
    matches.value.filter((m) => {
        const t = new Date(m.start_time).getTime();
        return (
            t >= windowStart.value.getTime() && t < windowEnd.value.getTime()
        );
    }),
);

function dayKey(d: Date): string {
    return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

function dayLabel(d: Date): string {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const that = new Date(d);
    that.setHours(0, 0, 0, 0);
    const diff = Math.round((that.getTime() - today.getTime()) / DAY);
    if (diff === 0) return "Today";
    if (diff === -1) return "Yesterday";
    if (diff === 1) return "Tomorrow";
    return d.toLocaleDateString([], {
        weekday: "short",
        day: "numeric",
        month: "short",
    });
}

const visibleGroups = computed(() => {
    const groups = new Map<
        string,
        { key: string; label: string; date: number; matches: Match[] }
    >();
    for (const m of visibleMatches.value) {
        const d = new Date(m.start_time);
        const key = dayKey(d);
        if (!groups.has(key)) {
            const dd = new Date(d);
            dd.setHours(0, 0, 0, 0);
            groups.set(key, {
                key,
                label: dayLabel(d),
                date: dd.getTime(),
                matches: [],
            });
        }
        groups.get(key)!.matches.push(m);
    }
    const arr = [...groups.values()].sort((a, b) => a.date - b.date);
    for (const g of arr) {
        g.matches.sort(
            (a, b) =>
                new Date(a.start_time).getTime() -
                new Date(b.start_time).getTime(),
        );
    }
    return arr;
});

const windowTitle = computed(() => {
    const s = windowStart.value;
    const e = new Date(windowEnd.value.getTime() - DAY);
    const sameMonth = s.getMonth() === e.getMonth();
    const month = (d: Date) => d.toLocaleDateString([], { month: "short" });
    if (sameMonth) {
        return `${s.getDate()}–${e.getDate()} ${month(e)}`;
    }
    return `${s.getDate()} ${month(s)} – ${e.getDate()} ${month(e)}`;
});
const windowSubtitle = computed(
    () => `${visibleMatches.value.length} matches this week`,
);

// ── Season FAQ ───────────────────────────────────────────────────────────────
// Backed by GET /api/leagues/{slug}/season-stats, which queries the same
// external providers the fetcher uses (see backend/services/season_stats.py) —
// not our own DB, which only ever holds a rolling window and can look empty
// right after a season ends and before the next one is announced.
const seasonFaq = computed(() => {
    if (!selectedLeague.value || !seasonStats.value) return null;
    const name = selectedLeague.value.name;
    const stats = seasonStats.value;

    if (!stats.published) {
        return {
            items: [
                {
                    question: `When does the ${name} season start?`,
                    answer: `Fixtures for the next ${name} season haven't been published yet. Check back soon — this updates automatically once they're announced.`,
                },
            ],
        };
    }

    const fmt = (d: Date) =>
        d.toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" });
    const start = stats.season_start ? fmt(new Date(stats.season_start)) : null;

    // Knockout cups (FA Cup, EFL Cup) draw each round only once the previous one
    // finishes — there's no fixed "games this season" total to report, so the
    // count means "currently scheduled", phrased to make that explicit.
    const countAnswer = stats.progressive_knockout
        ? `${stats.regular_season_count} ${stats.regular_season_count === 1 ? "match is" : "matches are"} currently scheduled for the ${name}. Later rounds are drawn as the competition progresses, so the full total isn't set yet.`
        : `The season contains ${stats.regular_season_count} matches before playoffs that we track.`;

    return {
        items: [
            ...(start
                ? [
                      {
                          question: `When does the ${name} season start?`,
                          answer: `The ${name} season starts on ${start}.`,
                      },
                  ]
                : []),
            {
                question: `How many games are in a ${name} season?`,
                answer: countAnswer,
            },
        ],
    };
});

watch(
    seasonFaq,
    (faq) => {
        if (!faq) {
            removeJsonLd("faq-jsonld");
            return;
        }
        setJsonLd("faq-jsonld", {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            mainEntity: faq.items.map((item) => ({
                "@type": "Question",
                name: item.question,
                acceptedAnswer: { "@type": "Answer", text: item.answer },
            })),
        });
    },
    { immediate: true },
);

// ── Modal ────────────────────────────────────────────────────────────────────
function openSportModal() {
    modalTeam.value = null;
    modalSport.value = selectedLeague.value?.sport ?? null;
    showModal.value = true;
}

async function onAddToCalendar(m: Match) {
    // Open the subscribe flow preselected to the home team (user can switch in the modal)
    if (m.home_slug) {
        try {
            modalTeam.value = await fetchTeam(m.home_slug, m.sport);
            modalSport.value = m.sport;
            showModal.value = true;
            return;
        } catch {
            /* fall through to sport-level modal */
        }
    }
    modalSport.value = m.sport;
    modalTeam.value = null;
    showModal.value = true;
}

function closeModal() {
    showModal.value = false;
    modalSport.value = null;
    modalTeam.value = null;
}

onMounted(async () => {
    sports.value = await fetchSports();
    if (!leagueOptions.value.length) return;

    const leagueParam = route.query.league as string | undefined;
    const filterParam = route.query.filter as string | undefined;

    // No explicit ?league= given — default to whatever the hero is currently
    // spotlighting (same scoring as the featured match), so "See all matches"
    // lands somewhere relevant instead of always the first league in the list.
    let defaultLeague = leagueOptions.value[0];
    if (!leagueParam) {
        if (cachedFeaturedMatch.value === undefined) {
            await refreshFeaturedMatch();
        }
        const fm = cachedFeaturedMatch.value;
        if (fm) {
            const match = leagueOptions.value.find(
                (l) => l.sport === fm.sport && l.slug === fm.league.slug,
            );
            if (match) defaultLeague = match;
        }
    }

    selectedLeague.value =
        leagueOptions.value.find((l) => l.slug === leagueParam) ?? defaultLeague;

    await loadTeams();

    if (filterParam && teamOptions.value.some((t) => t.slug === filterParam)) {
        selectedTeamSlug.value = filterParam;
    }

    await Promise.all([loadMatches(), loadSeasonStats()]);
    pushQuery(selectedLeague.value, selectedTeamSlug.value);

    try {
        const iso = await fetchLastUpdated();
        lastUpdatedAt.value = iso ? new Date(iso) : null;
    } catch {
        /* badge just won't show */
    }
    clockTimer = window.setInterval(() => (now.value = Date.now()), 15_000);
});

onUnmounted(() => {
    if (clockTimer !== null) window.clearInterval(clockTimer);
    removeJsonLd("faq-jsonld");
});

watch(weekOffset, () => {
    open.value = null;
});
</script>
