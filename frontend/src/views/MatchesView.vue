<template>
    <Navbar @get-started="openSportModal" />

    <main class="min-h-screen">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
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

            <div class="flex flex-wrap items-center gap-2.5 mb-8">
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

                <span class="filter-pill cursor-default">{{
                    season
                }}</span>

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

            <div v-if="open" class="fixed inset-0 z-10" @click="open = null" />

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

            <div v-else class="text-center py-16">
                <p class="font-semibold">No matches this week</p>
            </div>

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

    <Footer />

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
import { ref, computed, onMounted, onUnmounted, watch, h } from "vue";
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
import { saveLastLeague, readLastLeague } from "@/utils/lastLeagueStorage";
import { useResponsiveFilterMenu } from "@/composables/useResponsiveFilterMenu";
import { useWeekWindow, formatSessionTime } from "@/composables/useWeekWindow";
import { useSeasonLabel } from "@/composables/useSeasonLabel";
import { useLeagueEventsJsonLd } from "@/composables/useLeagueEventsJsonLd";
import Navbar from "@/components/Navbar.vue";
import Icon from "@/components/Icon.vue";
import TeamBadge from "@/components/TeamBadge.vue";
import MatchRow from "@/components/MatchRow.vue";
import TeamSelectorModal from "@/components/TeamSelectorModal.vue";
import StandingsModal from "@/components/StandingsModal.vue";
import MatchPreviewModal from "@/components/MatchPreviewModal.vue";
import Footer from "@/components/Footer.vue";

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
const initialLoad = ref(true);

const { open, leagueBtn, teamBtn, menuPositionStyle, toggle } = useResponsiveFilterMenu();

const {
    weekOffset,
    autoWeekOffset,
    windowStart,
    isMotorsportLeague,
    visibleGroups,
    windowTitle,
    windowSubtitle,
    jumpToRelevantWeek,
} = useWeekWindow(
    matches,
    computed(() => selectedLeague.value?.sport),
);

const season = useSeasonLabel(
    windowStart,
    computed(() => selectedLeague.value?.slug),
);

const showModal = ref(false);
const modalSport = ref<string | null>(null);
const modalTeam = ref<Team | null>(null);
const standingsMatch = ref<Match | null>(null);
const previewMatch = ref<Match | null>(null);

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

function pushQuery(league: LeagueOption | null, team: string | null) {
    const query: Record<string, string> = { ...(route.query as Record<string, string>) };
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

useLeagueEventsJsonLd(
    matches,
    leagueLock,
    computed(() => selectedLeague.value?.name ?? pageH1.value),
    computed(() => route.path),
);

function openSportModal() {
    modalTeam.value = null;
    modalSport.value = selectedLeague.value?.sport ?? null;
    showModal.value = true;
}

async function onAddToCalendar(m: Match) {
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
    if (route.query.wstep || route.query.wsport || route.query.wteam) {
        showModal.value = true;
    }

    try {
        sports.value = await fetchSports();
        if (!leagueOptions.value.length) return;

        const leagueParam = leagueLock.value ?? (route.query.league as string | undefined);
        const filterParam = route.query.filter as string | undefined;

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

        const matchedLeague = leagueOptions.value.find((l) => l.slug === leagueParam);
        selectedLeague.value = matchedLeague ?? (leagueLock.value ? null : defaultLeague);

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
});

watch(weekOffset, () => {
    open.value = null;
});
</script>
