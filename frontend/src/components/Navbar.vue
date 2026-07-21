<template>
    <div class="sticky top-0 z-50 flex justify-center px-3.5 sm:px-4 pt-3.5 sm:pt-4">
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
                class="flex items-center ml-auto rounded-2xl p-1 bg-white/5 border border-white/10"
            >
                <RouterLink
                    v-for="tab in tabs"
                    :key="tab.to"
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

<script setup lang="ts">
import { RouterLink } from "vue-router";

const emit = defineEmits<{ getStarted: [] }>();

const tabs = [
    { label: "Home", to: "/" }, //home
    { label: "Matches", to: "/matches" }, //matches — league defaults to the featured match's league
];
</script>
