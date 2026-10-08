# DeckVoice SaaS setup

## Stack
- **Auth:** Supabase (email/password)
- **Billing:** Paddle (merchant of record) — Checkout + customer portal
- **Database:** Postgres (Cloud SQL) + SaaS tables
- **Analytics:** PostHog (dashboard + marketing)

## Plans

Billing is metered on **meeting-minutes** — the time a bot actually spends in a
call — not on launch counts. A launch is unbounded cost: the Recall bot and the
realtime audio model both bill for as long as the bot stays in the meeting, so
counting launches cannot protect margin.

| Plan | Price | Meeting-minutes | Uploads | Concurrent | Max / meeting | Overage |
|------|-------|-----------------|---------|------------|---------------|---------|
| Free | $0 | 30 | 2 | 1 | 20 min | hard stop |
| Team | $99/mo | 600 (10 hr) | 25 | 3 | 90 min | $12/hr |
| Business | $399/mo | 3,000 (50 hr) | 200 | 10 | 180 min | $10/hr |
| Enterprise | contract | 12,000 | 1,000 | 40 | 240 min | $8/hr |

Legacy `starter` ($10) and `pro` ($20) are grandfathered at 120 and 300
meeting-minutes. They are no longer purchasable but still resolve on inbound
Paddle webhooks so existing subscribers keep working.

Plan definitions live in `backend/app/domain/plans.py`. `tests/test_plans.py`
asserts every tier prices above a conservative COGS floor — if you change a
price or an allowance, that test tells you whether the tier still makes money.

## Cost controls

Three independent layers, so no single failure leaves a bot billing forever:

1. **Plan ceiling** — `max_session_minutes` per plan.
2. **Recall `automatic_leave`** — sent on every bot at launch
   (`build_automatic_leave`). `in_call_recording_timeout` is the plan ceiling,
   so Recall ends the bot even if our backend is down. Also covers waiting
   rooms, nobody joining, everyone leaving, and prolonged silence.
3. **Watchdog** — `metering.watchdog_loop` runs in the API lifespan, scans live
   sessions every `SESSION_CLEANUP_INTERVAL_SECONDS`, and force-leaves anything
   past its ceiling.

Minutes are metered by `backend/app/domain/metering.py`: the window opens when
the bot enters the call and closes exactly once on a terminal status, on
operator leave, or by the watchdog. Partial minutes round up.

## Backend env (Cloud Run)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

PADDLE_API_KEY=pdl_live_apikey_...
PADDLE_WEBHOOK_SECRET=pdl_ntfset_...
PADDLE_CLIENT_TOKEN=live_...
PADDLE_API_BASE=https://api.paddle.com
PADDLE_PRICE_TEAM=pri_...
PADDLE_PRICE_BUSINESS=pri_...
# keep the old ids mapped for grandfathered subscribers
PADDLE_PRICE_STARTER=pri_...
PADDLE_PRICE_PRO=pri_...

MARKETING_URL=https://...
DASHBOARD_URL=https://...
OPEN_DEMO_ACCESS=false
PRESENTER_TOKEN_SECRET=random-long-secret
SESSION_CLEANUP_INTERVAL_SECONDS=60
```

`PADDLE_API_BASE` defaults to **live** in `config.py`. A deploy that forgets the
variable must not silently run billing against the sandbox.

## Paddle setup
1. Create products: DeckVoice Team ($99/mo) and DeckVoice Business ($399/mo)
2. Copy the price ids into `PADDLE_PRICE_TEAM` / `PADDLE_PRICE_BUSINESS`
3. Webhook: `POST /webhooks/paddle` — events: `transaction.completed`,
   `subscription.created`, `subscription.updated`, `subscription.past_due`,
   `subscription.canceled`
4. Inbound webhooks are signature-verified **and** source-IP allowlisted against
   Paddle's published list (`app/http/paddle_ips.py`)

## Supabase setup
1. Create project → enable Email auth
2. Copy URL, anon key, and JWT secret from Project Settings → API

## Frontend env (build-time)

Dashboard:
```
VITE_API_BASE=https://...
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_POSTHOG_KEY=phc_...
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

Marketing:
```
VITE_DASHBOARD_URL=https://...
VITE_POSTHOG_KEY=phc_...
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

Analytics no-op when `VITE_POSTHOG_KEY` is unset, so local dev and CI emit
nothing. Funnel event names are defined in `dashboard/src/lib/analytics.js` —
keep them stable, dashboards are built on them.

## Deploy order
1. API (`deploy/cloudbuild.api.yaml`) — set the Paddle and session env vars
2. Dashboard — add Supabase + PostHog Vite vars
3. Marketing (`deploy/cloudbuild.marketing.yaml`) — add PostHog Vite vars
