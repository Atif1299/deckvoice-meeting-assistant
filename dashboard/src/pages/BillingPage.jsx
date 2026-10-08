import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { apiGet, apiPost } from "../utils/api.js";
import { EVENTS, track } from "../lib/analytics.js";

const PADDLE_JS = "https://cdn.paddle.com/paddle/v2/paddle.js";

let paddleInit = null;
let paddleEventHandler = () => {};
const openedTransactions = new Set();

function loadPaddleScript() {
  if (window.Paddle) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector("script[data-paddle-js]");
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Paddle.js failed to load")));
      return;
    }
    const script = document.createElement("script");
    script.src = PADDLE_JS;
    script.async = true;
    script.dataset.paddleJs = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Paddle.js failed to load"));
    document.head.appendChild(script);
  });
}

function ensurePaddle(config) {
  if (!paddleInit) {
    paddleInit = loadPaddleScript().then(() => {
      if (config.environment === "sandbox") {
        window.Paddle.Environment.set("sandbox");
      }
      const init = {
        token: config.client_token,
        checkout: {
          settings: {
            successUrl: `${window.location.origin}/app/billing?checkout=success`,
          },
        },
        eventCallback: (event) => paddleEventHandler(event),
      };
      if (config.paddle_customer_id && String(config.paddle_customer_id).startsWith("ctm_")) {
        init.pwCustomer = { id: config.paddle_customer_id };
      }
      window.Paddle.Initialize(init);
    });
  }
  return paddleInit;
}

function openCheckout(transactionId) {
  if (!transactionId || !window.Paddle || openedTransactions.has(transactionId)) return;
  openedTransactions.add(transactionId);
  window.Paddle.Checkout.open({ transactionId });
}

const PLAN_COPY = {
  free: "Free includes 30 meeting-minutes and 2 deck uploads each month. No card required.",
  team: "Team includes 10 meeting-hours, 25 uploads, and 3 concurrent meetings. Extra time bills at $12/hour.",
  business: "Business includes 50 meeting-hours, 200 uploads, and 10 concurrent meetings. Extra time bills at $10/hour.",
  starter: "Starter is a legacy plan (120 meeting-minutes). Move to Team for more time and concurrency.",
  pro: "Pro is a legacy plan (300 meeting-minutes). Move to Team or Business for more time and concurrency.",
};

const UPGRADE_OPTIONS = [
  { plan: "team", label: "Upgrade to Team — $99/mo", variant: "button-primary" },
  { plan: "business", label: "Upgrade to Business — $399/mo", variant: "button-secondary" },
];

// Plans that can still reach the Paddle customer portal.
const PAID_PLANS = ["team", "business", "starter", "pro"];

function formatHours(minutes) {
  if (minutes < 60) return `${minutes} min`;
  const hours = minutes / 60;
  return `${Number.isInteger(hours) ? hours : hours.toFixed(1)} hr`;
}

function UsageBar({ label, used, limit, format = (v) => v, tone }) {
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const over = limit ? used > limit : false;
  return (
    <div className="usage-bar-block">
      <div className="usage-bar-head">
        <span>{label}</span>
        <span>
          {format(used)} / {format(limit)}
        </span>
      </div>
      <div className="usage-bar-track">
        <div
          className={`usage-bar-fill${over || tone === "warn" ? " is-over" : ""}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function BillingPage() {
  const { profile, refreshProfile } = useAuth();
  const [params] = useSearchParams();
  const [usage, setUsage] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");

  async function load() {
    const data = await apiGet("/api/v1/billing/usage");
    setUsage(data);
    if (refreshProfile) {
      await refreshProfile();
    }
  }

  useEffect(() => {
    paddleEventHandler = (event) => {
      if (event?.name === "checkout.completed") {
        track(EVENTS.CHECKOUT_COMPLETED, {});
        setMessage("Subscription updated — thank you!");
        load();
        setBusy("");
      }
      if (event?.name === "checkout.closed") {
        setBusy("");
      }
    };
  });

  useEffect(() => {
    load().catch((e) => setMessage(String(e.message || e)));
  }, []);

  useEffect(() => {
    if (params.get("checkout") === "success") {
      setMessage("Subscription updated — thank you!");
      load();
    }
  }, [params]);

  useEffect(() => {
    const txn = params.get("_ptxn");
    let cancelled = false;
    apiGet("/api/v1/billing/paddle-config")
      .then((config) => ensurePaddle(config))
      .then(() => {
        if (!cancelled && txn) openCheckout(txn);
      })
      .catch((e) => {
        if (!cancelled) setMessage(String(e.message || e));
      });
    return () => {
      cancelled = true;
    };
  }, [params]);

  async function checkout(plan) {
    setBusy(plan);
    setMessage("");
    track(EVENTS.UPGRADE_CLICKED, { plan });
    try {
      const config = await apiGet("/api/v1/billing/paddle-config");
      await ensurePaddle(config);
      const { url, transaction_id: transactionId } = await apiPost("/api/v1/billing/checkout", { plan });
      if (transactionId && window.Paddle) {
        openCheckout(transactionId);
        return;
      }
      window.location.href = url;
    } catch (e) {
      setMessage(String(e.message || e));
      setBusy("");
    }
  }

  async function portal() {
    setBusy("portal");
    track(EVENTS.PORTAL_OPENED, {});
    try {
      const { url } = await apiPost("/api/v1/billing/portal", {});
      window.location.href = url;
    } catch (e) {
      setMessage(String(e.message || e));
    } finally {
      setBusy("");
    }
  }

  const plan = usage?.plan || profile?.plan || "free";
  const minutes = usage?.meeting_minutes;
  const concurrency = usage?.concurrency;
  const overage = minutes?.overage || 0;
  const upgrades = UPGRADE_OPTIONS.filter((option) => option.plan !== plan);
  const showPortal = PAID_PLANS.includes(plan);

  return (
    <section className="page-section">
      <p className="eyebrow">Billing</p>
      <h1>Plan &amp; usage</h1>
      <p className="lede">
        Current plan: <strong className="plan-pill">{usage?.plan_label || plan}</strong>
      </p>
      {PLAN_COPY[plan] ? <p className="helper-text">{PLAN_COPY[plan]}</p> : null}

      {usage ? (
        <div className="card billing-card">
          <UsageBar
            label="Meeting time this month"
            used={minutes?.used ?? 0}
            limit={minutes?.limit ?? 0}
            format={formatHours}
          />
          <UsageBar
            label="Deck uploads this month"
            used={usage.uploads.used}
            limit={usage.uploads.limit}
          />
          {concurrency ? (
            <p className="helper-text">
              {concurrency.active} of {concurrency.limit} concurrent meeting
              {concurrency.limit === 1 ? "" : "s"} in use · each bot leaves automatically after{" "}
              {usage.max_session_minutes} minutes.
            </p>
          ) : null}
          {overage > 0 ? (
            <p className="banner-note">
              {minutes.overage_allowed
                ? `${formatHours(overage)} over your allowance — $${minutes.overage_usd.toFixed(2)} in overage this period.`
                : `You are ${formatHours(overage)} over your allowance. Upgrade to launch again.`}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="billing-actions">
        {upgrades.map((option) => (
          <button
            key={option.plan}
            type="button"
            className={`button ${option.variant}`}
            disabled={!!busy}
            onClick={() => checkout(option.plan)}
          >
            {busy === option.plan ? "Opening checkout…" : option.label}
          </button>
        ))}
        {showPortal ? (
          <button type="button" className="button button-ghost" disabled={!!busy} onClick={portal}>
            Manage subscription
          </button>
        ) : null}
      </div>

      {message ? <p className="banner-note">{message}</p> : null}
    </section>
  );
}
