// Marketing-site analytics. Separate app from the dashboard, so this is a
// deliberate small duplicate of dashboard/src/lib/analytics.js rather than a
// shared package — the two have different event vocabularies.
//
// No-ops when VITE_POSTHOG_KEY is unset.

import posthog from "posthog-js";

const KEY = import.meta.env.VITE_POSTHOG_KEY || "";
const HOST = import.meta.env.VITE_POSTHOG_HOST || "https://us.i.posthog.com";

let ready = false;

export function initAnalytics() {
  if (ready || !KEY) return;
  posthog.init(KEY, {
    api_host: HOST,
    person_profiles: "identified_only",
    capture_pageview: false,
    autocapture: true,
  });
  ready = true;
}

export function track(event, properties = {}) {
  if (!ready) return;
  posthog.capture(event, properties);
}

export function trackPageView(path) {
  if (!ready) return;
  posthog.capture("$pageview", { $current_url: window.location.origin + path });
}

export const EVENTS = {
  SIGNUP_CTA_CLICKED: "signup_cta_clicked",
  PRICING_VIEWED: "pricing_viewed",
  PLAN_CTA_CLICKED: "plan_cta_clicked",
};

/**
 * Capture the acquisition channel on first touch and keep it for the whole
 * visit, so a signup can be attributed to the campaign that produced it.
 * Without this, every organic and paid experiment is unmeasurable.
 */
export function captureAttribution() {
  if (typeof window === "undefined") return;
  try {
    if (sessionStorage.getItem("dv_attribution")) return;
    const params = new URLSearchParams(window.location.search);
    const attribution = {
      utm_source: params.get("utm_source") || "",
      utm_medium: params.get("utm_medium") || "",
      utm_campaign: params.get("utm_campaign") || "",
      utm_content: params.get("utm_content") || "",
      referrer: document.referrer || "",
      landing_path: window.location.pathname,
    };
    sessionStorage.setItem("dv_attribution", JSON.stringify(attribution));
  } catch {
    // Private mode or blocked storage — attribution is best-effort.
  }
}

export function getAttribution() {
  try {
    return JSON.parse(sessionStorage.getItem("dv_attribution") || "{}");
  } catch {
    return {};
  }
}
