// Product analytics. Deliberately thin: one module the whole app imports, so
// swapping providers or adding a destination is a single-file change.
//
// No-ops when VITE_POSTHOG_KEY is unset, so local dev and CI never emit events.

import posthog from "posthog-js";

const KEY = import.meta.env.VITE_POSTHOG_KEY || "";
const HOST = import.meta.env.VITE_POSTHOG_HOST || "https://us.i.posthog.com";

let ready = false;

export function initAnalytics() {
  if (ready || !KEY) return;
  posthog.init(KEY, {
    api_host: HOST,
    person_profiles: "identified_only",
    capture_pageview: false, // routed manually so SPA navigations are captured
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

export function identify(user) {
  if (!ready || !user?.user_id) return;
  posthog.identify(user.user_id, {
    email: user.email,
    workspace_id: user.workspace_id,
    plan: user.plan,
  });
  if (user.workspace_id) {
    posthog.group("workspace", user.workspace_id, {
      name: user.workspace_name,
      plan: user.plan,
    });
  }
}

export function resetAnalytics() {
  if (!ready) return;
  posthog.reset();
}

// The funnel that decides whether this business works. Keep these names stable
// — dashboards and the activation metric are built on them.
export const EVENTS = {
  SIGNED_UP: "signed_up",
  LOGGED_IN: "logged_in",
  DECK_UPLOAD_STARTED: "deck_upload_started",
  DECK_UPLOAD_SUCCEEDED: "deck_upload_succeeded",
  DECK_UPLOAD_FAILED: "deck_upload_failed",
  DECK_INDEXED: "deck_indexed",
  LAUNCH_ATTEMPTED: "launch_attempted",
  LAUNCH_SUCCEEDED: "launch_succeeded",
  LAUNCH_BLOCKED_BY_QUOTA: "launch_blocked_by_quota",
  SESSION_ENDED: "session_ended",
  UPGRADE_CLICKED: "upgrade_clicked",
  CHECKOUT_COMPLETED: "checkout_completed",
  PORTAL_OPENED: "portal_opened",
};
