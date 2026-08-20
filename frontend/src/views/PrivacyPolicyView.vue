<template>
    <LegalLayout title="Privacy policy" updated="13 July 2026">
        <section>
            <h2>Overview</h2>
            <p>
                MatchCalender provides live sports calendars you can subscribe
                to. This policy explains what data we collect when you use the
                site, why, and what we don't do. We built this product to be
                usable without an account, and we've kept data collection to the
                minimum that is required.
            </p>
        </section>

        <section>
            <h2>What we collect</h2>
            <ul>
                <li>
                    <strong>Your team/league/sport selections.</strong> When you
                    pick a team on the site, that choice is encoded directly
                    into the calendar link (URL) we generate for you and stored
                    in your browser's local storage so the site remembers your
                    last-viewed league. It is not tied to an account, an email
                    address, or any other identifier — we don't know who you
                    are.
                </li>
                <li>
                    <strong>Standard server logs.</strong> Like virtually every
                    website, our servers record request logs (IP address,
                    timestamp, requested URL, user agent) for security and
                    debugging. These logs are kept only as long as needed to
                    operate the service and are not used for tracking,
                    advertising, or sold to anyone.
                </li>
                <li>
                    <strong>Calendar app requests.</strong> When your calendar
                    app (Google Calendar, Apple Calendar, Outlook, etc.)
                    refreshes your subscribed feed, it makes a request to our
                    server the same way your browser does. We don't use this to
                    build a profile of you.
                </li>
            </ul>
        </section>

        <section>
            <h2>What we don't collect</h2>
            <ul>
                <li>No accounts, no passwords, no email addresses.</li>
                <li>No payment information — MatchCalender is free.</li>
                <li>
                    No advertising or third-party analytics/tracking scripts.
                </li>
                <li>
                    No cookies used for tracking (only your browser's local
                    storage, on your device, for the reason above).
                </li>
            </ul>
        </section>

        <section>
            <h2>Third-party content</h2>
            <p>
                Team crests and league data are sourced from public sports data
                providers and league websites, and some team badge images are
                loaded directly from those third parties' own servers. Loading
                those images causes your browser to make a request to that third
                party, subject to their own privacy practices — the same way
                loading an image from any external site would. We don't control
                those providers' data practices.
            </p>
        </section>

        <section>
            <h2>Your rights</h2>
            <p>
                Because we don't collect personal data tied to an identity,
                there's generally nothing to access, export, or delete on
                request. If you've saved a calendar link somewhere and want it
                to stop working, you can simply unsubscribe from it in your
                calendar app — we don't need to be involved.
            </p>
        </section>

        <section>
            <h2>Changes to this policy</h2>
            <p>
                If our data practices change (for example, if we introduce
                optional accounts in the future), we'll update this page and
                change the "last updated" date above.
            </p>
        </section>

        <section>
            <h2>Contact</h2>
            <p>
                Questions about this policy? Email
                <a href="mailto:support@matchcalender.com"
                    >support@matchcalender.com</a
                >.
            </p>
        </section>
    </LegalLayout>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import LegalLayout from "@/components/LegalLayout.vue";
</script>
