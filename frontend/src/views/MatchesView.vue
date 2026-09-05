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
                {{ pageH1 }}
            </h1>
            <p class="mb-2 max-w-xl" style="color: var(--ms-muted)">
                {{ pageIntro }}
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
                <!-- League — a fixed label on league landing pages, a picker elsewhere -->
                <span v-if="leagueLock" class="filter-pill active cursor-default">
                    {{ selectedLeague?.name ?? "League" }}
                </span>
                <div v-else class="relative">
                    <button
                        ref="leagueBtn"
                        class="filter-pill active"
                        @click="toggle('league')"
                    >
                        {{ selectedLeague?.name ?? "League" }}
                        <ChevronDown />
                    </button>
                    <div v-if="open === 'league'" class="filter-menu max-h-72 overflow-y-auto" :style="menuPositionStyle">
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
                        ref="teamBtn"
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
                        :style="menuPositionStyle"
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
                    v-if="selectedTeamSlug || weekOffset !== autoWeekOffset"
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

            <!-- Loading: mirrors the real group cards below (header strip +
                 rows) so the page doesn't reflow when matches arrive. -->
            <template v-if="loading || initialLoad">
                <div
                    v-for="g in 2"
                    :key="`group-skeleton-${g}`"
                    class="glass-card rounded-[24px] overflow-hidden mb-3.5"
                    aria-hidden="true"
                >
                    <div
                        class="flex items-center justify-between px-4 sm:px-6 py-3.5 bg-white/[0.05] border-b border-white/[0.08]"
                    >
                        <span class="ms-skeleton" style="width: 104px; height: 14px"></span>
                        <span class="ms-skeleton" style="width: 62px; height: 12px"></span>
                    </div>
                    <div
                        v-for="r in 3"
                        :key="`row-skeleton-${r}`"
                        class="flex items-center gap-3 px-4 sm:px-6 py-4 border-b border-white/[0.06] last:border-b-0"
                    >
                        <span class="ms-skeleton flex-none" style="width: 38px; height: 38px; border-radius: 11px"></span>
                        <div class="min-w-0 flex-1">
                            <span class="ms-skeleton block" style="width: 58%; height: 14px"></span>
                            <span class="ms-skeleton block" style="width: 36%; height: 11px; margin-top: 7px"></span>
                        </div>
                        <span class="ms-skeleton flex-none" style="width: 46px; height: 15px"></span>
                    </div>
                </div>
            </template>

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
                        <span
                            v-if="!isMotorsportLeague"
                            class="text-xs font-semibold"
                            style="color: rgba(244,247,251,.45)"
                            >{{ group.matches.length }}
                            {{
                                group.matches.length === 1 ? "match" : "matches"
                            }}</span
                        >
                    </div>
                    <div v-if="isMotorsportLeague">
                        <div
                            v-for="m in group.matches"
                            :key="m.id"
                            class="flex items-center justify-between px-4 sm:px-6 py-3.5 border-b border-white/[0.06] last:border-b-0"
                        >
                            <span class="font-bold text-sm" style="color: rgba(244,247,251,.6)">{{ m.away_team }}</span>
                            <span class="font-bold text-sm">{{ formatSessionTime(m.start_time) }}</span>
                        </div>
                    </div>
                    <div v-else>
                        <MatchRow
                            v-for="m in group.matches"
                            :key="m.id"
                            :match="m"
                            @add="onAddToCalendar"
                            @view-standings="onViewStandings"
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
        </div>
    </main>

    <TeamSelectorModal
        v-if="showModal"
        :initial-sport="modalSport"
        :initial-team="modalTeam"
        @close="closeModal"
    />

    <MatchPreviewModal
        v-if="previewMatch"
        :match="previewMatch"
        @close="previewMatch = null"
        @view-full-standings="openFullStandings"
    />

    <StandingsModal
        v-if="standingsMatch"
        :league-slug="standingsMatch.league.slug"
        :league-name="standingsMatch.league.name"
        :home-team="standingsMatch.home_team"
        :away-team="standingsMatch.away_team"
        @close="standingsMatch = null"
    />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick, h } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { League, Match, Sport, Team } from "@/types";
import {
    fetchSports,
    fetchTeams,
    fetchTeam,
    fetchMatches,
    fetchLastUpdated,
} from "@/services/sports";
import { cachedFeaturedMatch, refreshFeaturedMatch } from "@/services/featuredMatchCache";
import { setJsonLd, removeJsonLd } from "@/utils/seo";
import Navbar from "@/components/Navbar.vue";
import Icon from "@/components/Icon.vue";
import TeamBadge from "@/components/TeamBadge.vue";
import MatchRow from "@/components/MatchRow.vue";
import TeamSelectorModal from "@/components/TeamSelectorModal.vue";
import StandingsModal from "@/components/StandingsModal.vue";
import MatchPreviewModal from "@/components/MatchPreviewModal.vue";

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

// Remembers whichever league was last actually shown here — set both by a
// manual pick from the dropdown and by arriving via an explicit ?league=
// (e.g. the hero's "See all matches" link) — so the plain "Matches" nav tab
// (no query at all) resumes wherever you last were, instead of always
// resetting to the hero's current pick. Only the hero link and the very
// first-ever visit fall back to the featured league.
const LAST_LEAGUE_KEY = "ms:last-league";

function saveLastLeague(opt: LeagueOption) {
    localStorage.setItem(LAST_LEAGUE_KEY, JSON.stringify({ sport: opt.sport, slug: opt.slug }));
}

function readLastLeague(): { sport: string; slug: string } | null {
    try {
        const raw = localStorage.getItem(LAST_LEAGUE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

const route = useRoute();
const router = useRouter();

// League landing pages (e.g. /premier-league) reuse this view but lock it to a
// single league and swap in their own SEO copy — see src/data/leaguePages.json
// and the route meta in src/router/index.ts.
const leagueLock = computed(() => (route.meta.leagueSlug as string | undefined) ?? null);
const pageH1 = computed(() => (route.meta.h1 as string | undefined) ?? "All matches");
const pageIntro = computed(
    () => (route.meta.intro as string | undefined) ?? "Browse every fixture by league or team.",
);

const sports = ref<Sport[]>([]);
const selectedLeague = ref<LeagueOption | null>(null);
const teamOptions = ref<Team[]>([]);
const selectedTeamSlug = ref<string | null>(null);
const matches = ref<Match[]>([]);
const loading = ref(false);
// Separate from `loading` because the first paint happens before onMounted
// has resolved a league at all — and loadMatches() early-returns without
// touching `loading` when there's no league yet. Without this the page shows
// "No matches this week" for a beat before the real fetch even starts.
const initialLoad = ref(true);
const open = ref<"league" | "team" | null>(null);
// Each filter-menu is `position: absolute` inside its own button's tiny
// wrapper, so its default left/right anchor is wherever that specific pill
// landed in the flex-wrap row — fine near the left margin, but on a phone
// "All teams" sometimes fits on the same line as League/Season (no wrap),
// landing near the *right* edge, and the dropdown then opens off-screen with
// only the crest column visible and the team names cut off. Below the mobile
// breakpoint we switch the open menu to `position: fixed`, spanning the
// viewport with a fixed margin, and set its top from the trigger button's
// real position — independent of which pill happened to be nearest the edge.
const leagueBtn = ref<HTMLButtonElement | null>(null);
const teamBtn = ref<HTMLButtonElement | null>(null);
const isNarrowScreen = ref(false);
const menuTop = ref(0);
function updateIsNarrowScreen() {
    isNarrowScreen.value = window.innerWidth <= 639;
}
const menuPositionStyle = computed(() =>
    isNarrowScreen.value
        ? {
              position: "fixed" as const,
              top: `${menuTop.value}px`,
              left: "0.75rem",
              right: "0.75rem",
              maxWidth: "none",
              minWidth: "0",
              // `fixed` pulls the menu out of document flow, so it can no
              // longer grow the page's own scroll the way the old `absolute`
              // positioning did — cap it to whatever viewport space is left
              // below the button (with a floor so it isn't squashed to
              // nothing near the bottom of the screen) and let it scroll
              // internally instead.
              maxHeight: `${Math.max(160, window.innerHeight - menuTop.value - 12)}px`,
          }
        : {},
);
// Being `fixed` also decouples the menu from page scroll — without this, the
// content behind it keeps scrolling under a menu that stays visually pinned
// in place. Only needed in the mobile/fixed mode; on desktop the menu is
// still `absolute` inside the page flow and scrolls along with it normally.
watch(open, (which) => {
    if (!isNarrowScreen.value) return;
    if (which) {
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
        document.body.style.overflow = "hidden";
        if (scrollbarWidth > 0) document.body.style.paddingRight = `${scrollbarWidth}px`;
    } else {
        document.body.style.overflow = "";
        document.body.style.paddingRight = "";
    }
});
const weekOffset = ref(0);
// The week jumpToRelevantWeek() picked on its own for the current league.
// Reset compares against this rather than 0: a league whose next fixture is
// months out (e.g. the Champions League final) legitimately opens on a
// non-zero offset, and that isn't something the visitor chose to undo.
const autoWeekOffset = ref(0);

// Modal state (reuses the home subscribe flow)
const showModal = ref(false);
const modalSport = ref<string | null>(null);
const modalTeam = ref<Team | null>(null);
const standingsMatch = ref<Match | null>(null);
const previewMatch = ref<Match | null>(null);

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
    // F1's season doesn't roll over mid-year like the others — it's just
    // whatever the current calendar year is, always (threshold: 0 + atStart
    // means "current month >= 0" is always true, so `start` is always `y`).
    "formula-1": { threshold: 0, atStart: true, singleYear: true },
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
    const wasOpen = open.value === which;
    open.value = wasOpen ? null : which;
    if (wasOpen) return;
    nextTick(() => {
        const btn = which === "league" ? leagueBtn.value : teamBtn.value;
        if (btn) menuTop.value = btn.getBoundingClientRect().bottom + 8;
    });
}

function pushQuery(league: LeagueOption | null, team: string | null) {
    // Merge so the subscribe-wizard params (wstep/wsport/wteam) survive when the
    // modal is open on top of the matches page.
    const query: Record<string, string> = { ...(route.query as Record<string, string>) };
    // On a locked league page the league lives in the path, not the query.
    if (league?.slug && !leagueLock.value) query.league = league.slug;
    else delete query.league;
    if (team) query.filter = team;
    else delete query.filter;
    router.replace({ query });
}

function clearWizardQuery() {
    const query = { ...route.query };
    delete query.wstep;
    delete query.wsport;
    delete query.wteam;
    router.replace({ query });
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
    saveLastLeague(opt);
    pushQuery(opt, null);
    await Promise.all([loadTeams(), loadMatches()]);
}

function selectTeam(slug: string | null) {
    open.value = null;
    selectedTeamSlug.value = slug;
    pushQuery(selectedLeague.value, slug);
    loadMatches();
}

function resetFilters() {
    selectedTeamSlug.value = null;
    // Back to the week the pager opened on, not week 0 — for an off-season
    // league that would land the visitor on an empty week.
    weekOffset.value = autoWeekOffset.value;
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
        autoWeekOffset.value = 0;
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
    autoWeekOffset.value = weekOffset.value;
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

// Motorsport isn't a day-by-day fixture list — each Grand Prix is a single
// weekend of sessions (Practice/Qualifying/Race), so it groups by "home_team"
// (the Grand Prix — see tasks/fetcher.py's F1Filter) instead of by day.
const isMotorsportLeague = computed(() => selectedLeague.value?.sport === "motorsport");

function formatSessionTime(iso: string): string {
    return new Date(iso).toLocaleString([], {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).replace(",", "");
}

// Round numbers aren't in the API response — derived from the full season's
// fetch (not just the visible week) so "R7" stays correct regardless of which
// week you're currently looking at.
const meetingRounds = computed(() => {
    const earliest = new Map<string, number>();
    for (const m of matches.value) {
        const t = new Date(m.start_time).getTime();
        const prev = earliest.get(m.home_team);
        if (prev === undefined || t < prev) earliest.set(m.home_team, t);
    }
    const ordered = [...earliest.entries()].sort((a, b) => a[1] - b[1]);
    return new Map(ordered.map(([name], i) => [name, i + 1]));
});

const visibleGroups = computed(() => {
    if (isMotorsportLeague.value) {
        const groups = new Map<
            string,
            { key: string; label: string; date: number; matches: Match[] }
        >();
        for (const m of visibleMatches.value) {
            const key = m.home_team;
            if (!groups.has(key)) {
                const round = meetingRounds.value.get(m.home_team);
                groups.set(key, {
                    key,
                    label: round ? `Round ${round} · ${m.home_team}` : m.home_team,
                    date: new Date(m.start_time).getTime(),
                    matches: [],
                });
            }
            const g = groups.get(key)!;
            g.matches.push(m);
            g.date = Math.min(g.date, new Date(m.start_time).getTime());
        }
        const arr = [...groups.values()].sort((a, b) => a.date - b.date);
        for (const g of arr) {
            g.matches.sort(
                (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
            );
        }
        return arr;
    }

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

// ── SportsEvent structured data (league landing pages only) ──────────────────
// An ItemList of upcoming fixtures as schema.org SportsEvent — drives event
// rich results.

const SITE_URL = "https://matchcalender.com";

// Nominal broadcast-to-broadcast length per sport, used only for `endDate`.
// Google requires an end time for event rich results, but no upstream feed we
// use publishes one, so this is the scheduled slot rather than the final
// whistle — an over-run or a delayed start won't move it.
const EVENT_DURATION_MS: Record<string, number> = {
    football: 2 * 60 * 60 * 1000, // 90' + half-time + stoppage
    hockey: 2.5 * 60 * 60 * 1000, // 3 × 20' + two intermissions
    basketball: 2 * 60 * 60 * 1000,
    motorsport: 2 * 60 * 60 * 1000, // a session, not the whole race weekend
};
const DEFAULT_DURATION_MS = 2 * 60 * 60 * 1000;

function eventImage(m: Match): string {
    // Crest URLs are absolute and served by the league/provider CDNs; the
    // cropped variants point at our own API and some sources give us nothing,
    // so fall back to the social card rather than emit a relative URL.
    const crest = m.home_icon ?? m.away_icon;
    return crest && /^https?:\/\//.test(crest)
        ? crest
        : `${SITE_URL}/logo-social.png`;
}

watch(
    [matches, leagueLock],
    () => {
        if (!leagueLock.value) {
            removeJsonLd("league-events-jsonld");
            return;
        }
        const DAY_MS = 86_400_000;
        const now = Date.now();
        const upcoming = [...matches.value]
            .filter((m) => new Date(m.start_time).getTime() >= now - 3 * DAY_MS)
            // Google treats an Event with no `location` as invalid, so it earns
            // no rich result either way — emitting it would only add a Search
            // Console error. Two feeds (IIHF, Allsvenskan) carry no venue at
            // all, so their fixtures are held back rather than published broken.
            .filter((m) => !!m.venue)
            .sort(
                (a, b) =>
                    new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
            )
            .slice(0, 25);
        if (!upcoming.length) {
            removeJsonLd("league-events-jsonld");
            return;
        }
        const leagueName = selectedLeague.value?.name ?? pageH1.value;
        setJsonLd("league-events-jsonld", {
            "@context": "https://schema.org",
            "@type": "ItemList",
            itemListElement: upcoming.map((m, i) => {
                const teams = [
                    { "@type": "SportsTeam", name: m.home_team },
                    { "@type": "SportsTeam", name: m.away_team },
                ];
                const start = new Date(m.start_time);
                const end = new Date(
                    start.getTime() +
                        (EVENT_DURATION_MS[m.sport] ?? DEFAULT_DURATION_MS),
                );
                return {
                    "@type": "ListItem",
                    position: i + 1,
                    item: {
                        "@type": "SportsEvent",
                        name: `${m.home_team} vs ${m.away_team}`,
                        description: `${leagueName}: ${m.home_team} vs ${m.away_team} at ${m.venue} on ${start.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}. Sync the fixture to your calendar with MatchCalender.`,
                        startDate: m.start_time,
                        endDate: end.toISOString(),
                        eventStatus: "https://schema.org/EventScheduled",
                        eventAttendanceMode:
                            "https://schema.org/OfflineEventAttendanceMode",
                        image: eventImage(m),
                        location: { "@type": "Place", name: m.venue },
                        // `competitor` is the sport-specific property; Google's
                        // Event rich-result docs look for `performer`, so both
                        // carry the same two teams.
                        competitor: teams,
                        performer: teams,
                        organizer: {
                            "@type": "Organization",
                            name: leagueName,
                            url: `${SITE_URL}${route.path}`,
                        },
                    },
                };
            }),
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
    clearWizardQuery();
}

function onViewStandings(m: Match) {
    previewMatch.value = m;
}

function openFullStandings() {
    if (!previewMatch.value) return;
    standingsMatch.value = previewMatch.value;
    previewMatch.value = null;
}

onMounted(async () => {
    updateIsNarrowScreen();
    window.addEventListener("resize", updateIsNarrowScreen);

    // Reopen the subscribe wizard if the URL still carries its state (reload while open).
    if (route.query.wstep || route.query.wsport || route.query.wteam) {
        showModal.value = true;
    }

    // finally, not a trailing assignment: loadTeams() and fetchSports()
    // can both reject, and an aborted onMounted would otherwise leave the
    // skeleton on screen forever instead of falling through to the empty
    // state.
    try {
        sports.value = await fetchSports();
        if (!leagueOptions.value.length) return;

        // Locked league pages take the league from route meta; everywhere else it
        // comes from ?league= (falling back to last-picked / featured below).
        const leagueParam = leagueLock.value ?? (route.query.league as string | undefined);
        const filterParam = route.query.filter as string | undefined;

        // No explicit ?league= given (e.g. the Navbar's plain "Matches" tab) —
        // resume whatever league was last actually shown here; only fall back to
        // the hero's featured league if nothing's ever been shown yet.
        let defaultLeague = leagueOptions.value[0];
        if (!leagueParam) {
            const last = readLastLeague();
            const lastMatch = last
                ? leagueOptions.value.find((l) => l.sport === last.sport && l.slug === last.slug)
                : undefined;
            if (lastMatch) {
                defaultLeague = lastMatch;
            } else {
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
        }

        // On a locked league page, never silently fall back to another league — if
        // its fixtures aren't loaded yet, show an empty state under the right title.
        const matchedLeague = leagueOptions.value.find((l) => l.slug === leagueParam);
        selectedLeague.value = matchedLeague ?? (leagueLock.value ? null : defaultLeague);

        // An explicit ?league= (e.g. the hero's "See all matches" link) is a real
        // "show me this league" action too — remember it the same as a manual
        // pick, so the next plain "Matches" visit resumes here rather than
        // reverting to whatever was picked before this visit.
        if (matchedLeague && !leagueLock.value) saveLastLeague(matchedLeague);

        await loadTeams();

        if (filterParam && teamOptions.value.some((t) => t.slug === filterParam)) {
            selectedTeamSlug.value = filterParam;
        }

        await loadMatches();
        pushQuery(selectedLeague.value, selectedTeamSlug.value);
    } finally {
        initialLoad.value = false;
    }

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
    window.removeEventListener("resize", updateIsNarrowScreen);
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
    removeJsonLd("league-events-jsonld");
});

watch(weekOffset, () => {
    open.value = null;
});
</script>
