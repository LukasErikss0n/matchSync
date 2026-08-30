<template>
    <div
        class="nav-shell sticky top-0 z-50 flex justify-center px-3.5 sm:px-4 pt-3.5 sm:pt-4"
        :class="{ 'nav-shell-hidden': navHidden }"
    >
        <nav
            class="glass-nav flex items-center gap-3 sm:gap-5 w-full max-w-5xl px-2 sm:px-5 py-2 sm:py-2.5 rounded-3xl"
        >
            <RouterLink to="/" class="flex items-center gap-2.5 flex-shrink-0 pl-1">
                <div
                    class="w-8 h-8 rounded-[10px] flex items-center justify-center flex-shrink-0"
                    style="background: #131c2e; border: 1px solid rgba(142, 205, 242, 0.35)"
                >
                    <img
                        src="/logo.svg"
                        alt="MatchCalender"
                        class="w-full h-full object-contain"
                    />
                </div>
                <span class="hidden sm:inline font-extrabold text-[15px] tracking-tight whitespace-nowrap">
                    Match<span class="ms-text-accent">Calender</span>
                </span>
            </RouterLink>

            <nav
                class="relative flex items-center ml-auto rounded-2xl p-1"
            >
                <div
                    class="ms-tab-slider ms-tab-slider--outline"
                    :style="sliderStyle"
                ></div>
                <RouterLink
                    v-for="tab in tabs"
                    :key="tab.to"
                    ref="tabRefs"
                    :to="tab.to"
                    class="ms-tab text-[12.5px] sm:text-[13.5px] font-semibold px-3 sm:px-4 py-2 rounded-[11px] transition-colors whitespace-nowrap"
                    exact-active-class="ms-tab-active"
                >
                    {{ tab.label }}
                </RouterLink>
            </nav>

            <button
                class="ms-btn-primary flex items-center rounded-2xl px-3 sm:px-4 py-2 sm:py-2.5 text-[12px] sm:text-[13px] font-bold whitespace-nowrap"
                @click="emit('getStarted')"
            >
                Get calendar
            </button>
        </nav>
    </div>
</template>

<script lang="ts">
// The router keys each view by path, so Navbar itself is fully remounted on
// every navigation. Module scope (unlike <script setup>'s per-instance scope)
// survives that remount, so the pill can snap to where it "already was"
// before animating to the new tab, instead of every navigation looking like
// a fresh slide-in from the left.
let lastActiveIndex = 0;
let everMounted = false;
</script>

<script setup lang="ts">
import { RouterLink, useRoute } from "vue-router";
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

const emit = defineEmits<{ getStarted: [] }>();

// Hide on scroll-down, reveal on scroll-up — both driven by the same CSS
// transition duration (see .nav-shell), so hiding and revealing happen at
// the same speed. Only kicks in past a small threshold so the bar doesn't
// flicker away on a tiny scroll right at the top of the page.
const SCROLL_HIDE_THRESHOLD = 80;
const navHidden = ref(false);
let lastScrollY = 0;
let scrollTicking = false;

function updateNavVisibility() {
    const y = window.scrollY;
    if (y <= SCROLL_HIDE_THRESHOLD) {
        navHidden.value = false;
    } else if (y > lastScrollY) {
        navHidden.value = true; // scrolling down
    } else if (y < lastScrollY) {
        navHidden.value = false; // scrolling up
    }
    lastScrollY = y;
    scrollTicking = false;
}

function onScroll() {
    if (scrollTicking) return;
    scrollTicking = true;
    requestAnimationFrame(updateNavVisibility);
}

const tabs = [
    { label: "Home", to: "/" }, //home
    { label: "Matches", to: "/matches" }, //matches — league defaults to the featured match's league
];

const route = useRoute();
const activeIndex = ref(0);
const tabRefs = ref<{ $el: HTMLElement }[]>([]);
const sliderStyle = reactive({ width: "0px", transform: "translateX(0px)", opacity: "0", transition: "none" });

function targetIndex(): number {
    if (route.meta.isLeaguePage) return tabs.findIndex((t) => t.to === "/matches");
    const i = tabs.findIndex((t) => t.to === route.path);
    return i === -1 ? 0 : i;
}

function applyStyle(i: number, animate: boolean) {
    const el = tabRefs.value[i]?.$el as HTMLElement | undefined;
    if (!el) return;
    sliderStyle.transition = animate ? "" : "none";
    sliderStyle.width = `${el.offsetWidth}px`;
    sliderStyle.transform = `translateX(${el.offsetLeft}px)`;
    sliderStyle.opacity = "1";
}

watch(
    () => route.path,
    async () => {
        const target = targetIndex();
        activeIndex.value = target;
        lastActiveIndex = target;
        await nextTick();
        requestAnimationFrame(() => applyStyle(target, true));
    },
);

onMounted(async () => {
    await nextTick();
    const target = targetIndex();
    activeIndex.value = target;

    if (everMounted) {
        // Snap instantly to the previous instance's last position, then let
        // the browser paint that before animating to the real target.
        applyStyle(lastActiveIndex, false);
        requestAnimationFrame(() => requestAnimationFrame(() => applyStyle(target, true)));
    } else {
        applyStyle(target, false);
    }

    everMounted = true;
    lastActiveIndex = target;
    window.addEventListener("resize", () => applyStyle(activeIndex.value, false));

    // Seeded from the real scroll position (not 0) since Navbar remounts on
    // every navigation — a mid-page remount shouldn't read as "just
    // scrolled down" and hide itself immediately.
    lastScrollY = window.scrollY;
    window.addEventListener("scroll", onScroll, { passive: true });
});

onBeforeUnmount(() => {
    window.removeEventListener("scroll", onScroll);
});
</script>

<style scoped>
/* Same treatment as Hero.vue's sport tabs: flat, no filled pill — just a
   straight-edged underline on the active tab. */
.ms-tab-slider--outline {
    background: transparent;
    border: none;
    box-shadow: none;
}

.ms-tab-slider--outline::after {
    content: "";
    position: absolute;
    left: 14%;
    right: 14%;
    bottom: 4px;
    height: 3px;
    background: var(--ms-blue);
}

/* One transition, one duration, for both directions — hiding on scroll-down
   and revealing on scroll-up move at the identical speed. */
.nav-shell {
    transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.22s ease;
}

.nav-shell-hidden {
    transform: translateY(-130%);
    opacity: 0;
    pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
    .nav-shell {
        transition: opacity 0.15s ease;
    }
    .nav-shell-hidden {
        transform: none;
    }
}
</style>
