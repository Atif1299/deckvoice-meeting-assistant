# DeckVoice folder structure

This repo is four apps plus shared deploy/docs. Generated folders are omitted from the tree: `.git`, `node_modules`, `__pycache__`, `.vite`, `dist`, `.pytest_cache`. `.agents/` is Cursor agent skills (thousands of files) and is collapsed.

## Apps at a glance

| Folder | What it is |
|--------|------------|
| `backend/` | FastAPI API: auth, billing, decks, sessions, Recall, Gemini Live, webhooks |
| `dashboard/` | Operator UI (Vite + React): login, upload, launch, live session, billing |
| `marketing/` | Public site: homepage, pricing, legal pages |
| `presenter/` | Meeting-camera tab: slides + live agent (what Recall screenshares) |
| `deploy/` | Cloud Build YAML for Cloud Run |
| `docs/` | Architecture, partner packs, meeting notes |

## Tree

```
overtone-meeting-assistant/
|-- .agents/
|   `-- (agent skills; omitted)
|-- .github/
|   `-- workflows/
|       `-- deploy-backend-cloud-run.yml
|-- backend/
|   |-- alembic/
|   |   |-- versions/
|   |   |   |-- 001_saas_tables.py
|   |   |   `-- 002_paddle_subscription_columns.py
|   |   `-- env.py
|   |-- app/
|   |   |-- db/
|   |   |   |-- __init__.py
|   |   |   |-- migrate_legacy.py
|   |   |   |-- models.py
|   |   |   `-- schema_upgrade.py
|   |   |-- domain/
|   |   |   |-- __init__.py
|   |   |   |-- agents.py
|   |   |   |-- plans.py
|   |   |   |-- session_store.py
|   |   |   |-- usage.py
|   |   |   `-- workspaces.py
|   |   |-- http/
|   |   |   |-- __init__.py
|   |   |   |-- agents.py
|   |   |   |-- auth.py
|   |   |   |-- auth_routes.py
|   |   |   |-- billing.py
|   |   |   |-- customers.py
|   |   |   |-- me.py
|   |   |   |-- paddle_ips.py
|   |   |   |-- presentations.py
|   |   |   |-- sessions.py
|   |   |   |-- supabase_auth.py
|   |   |   `-- webhooks.py
|   |   |-- indexing/
|   |   |   |-- __init__.py
|   |   |   |-- converter.py
|   |   |   |-- embeddings.py
|   |   |   |-- pipeline.py
|   |   |   |-- vector_store.py
|   |   |   `-- vision.py
|   |   |-- meetings/
|   |   |   |-- __init__.py
|   |   |   `-- recall.py
|   |   |-- realtime/
|   |   |   |-- __init__.py
|   |   |   |-- gemini_live.py
|   |   |   |-- relay.py
|   |   |   |-- retrieval.py
|   |   |   |-- tools.py
|   |   |   |-- turn_routing.py
|   |   |   `-- ws_hub.py
|   |   |-- security/
|   |   |   |-- __init__.py
|   |   |   `-- presenter_token.py
|   |   |-- storage/
|   |   |   |-- __init__.py
|   |   |   `-- gcs.py
|   |   |-- __init__.py
|   |   |-- config.py
|   |   `-- main.py
|   |-- data/
|   |   `-- presentations/
|   |       |-- nav-test-pres/
|   |       |   `-- pages/
|   |       `-- pub-meta-test/
|   |           |-- pages/
|   |           `-- meta.json
|   |-- tests/
|   |   |-- test_bootstrap_workspace.py
|   |   |-- test_cors_origins.py
|   |   |-- test_delete_presentation.py
|   |   |-- test_health.py
|   |   |-- test_navigate_broadcast.py
|   |   |-- test_open_demo_access.py
|   |   |-- test_paddle_billing.py
|   |   |-- test_plans.py
|   |   |-- test_quality_gate.py
|   |   |-- test_relay_tool_cancel.py
|   |   |-- test_retrieval.py
|   |   |-- test_session_latency.py
|   |   `-- test_turn_routing.py
|   |-- .env.example
|   |-- alembic.ini
|   |-- Dockerfile
|   `-- requirements.txt
|-- dashboard/
|   |-- .artifacts/
|   |-- nginx/
|   |   `-- templates/
|   |       `-- default.conf.template
|   |-- public/
|   |   |-- media/
|   |   |   `-- logos/
|   |   |-- apple-touch-icon.png
|   |   |-- favicon.svg
|   |   |-- logo-mark.png
|   |   |-- logo-wordmark.png
|   |   `-- og-image.png
|   |-- src/
|   |   |-- components/
|   |   |   |-- AuthLayout.jsx
|   |   |   |-- BotConfigForm.jsx
|   |   |   |-- BrandLogo.jsx
|   |   |   |-- DeckVoiceMark.jsx
|   |   |   |-- FileUploader.jsx
|   |   |   |-- IndexingProgress.jsx
|   |   |   |-- integrations.js
|   |   |   |-- LiveTranscript.jsx
|   |   |   |-- PlatformLogo.jsx
|   |   |   `-- ProtectedRoute.jsx
|   |   |-- context/
|   |   |   `-- AuthContext.jsx
|   |   |-- lib/
|   |   |   |-- authRedirect.js
|   |   |   |-- sessionExpiry.js
|   |   |   `-- supabase.js
|   |   |-- pages/
|   |   |   |-- AdminPage.jsx
|   |   |   |-- AgentsPage.jsx
|   |   |   |-- AuthCallbackPage.jsx
|   |   |   |-- BillingPage.jsx
|   |   |   |-- ForgotPasswordPage.jsx
|   |   |   |-- LaunchPage.jsx
|   |   |   |-- LoginPage.jsx
|   |   |   |-- OverviewPage.jsx
|   |   |   |-- ResetPasswordPage.jsx
|   |   |   |-- SessionPage.jsx
|   |   |   |-- SignupPage.jsx
|   |   |   |-- Testform.jsx
|   |   |   `-- UploadPage.jsx
|   |   |-- utils/
|   |   |   `-- api.js
|   |   |-- App.jsx
|   |   |-- config.js
|   |   |-- index.css
|   |   |-- main.jsx
|   |   `-- platforms.js
|   |-- tests/
|   |   `-- e2e/
|   |       `-- admin-smoke.spec.js
|   |-- Dockerfile
|   |-- index.html
|   |-- package.json
|   |-- playwright.config.js
|   `-- vite.config.js
|-- deploy/
|   |-- cloudbuild.api.yaml
|   |-- cloudbuild.dashboard.build.yaml
|   |-- cloudbuild.dashboard.yaml
|   |-- cloudbuild.marketing.yaml
|   |-- cloudbuild.presenter.build.yaml
|   |-- cloudbuild.presenter.yaml
|   |-- DEPLOY.md
|   |-- live-test-results.json
|   `-- run_live_tests.ps1
|-- docs/
|   |-- assets/
|   |   `-- banner.svg
|   |-- outbound/
|   |   |-- generate_partner_docs.py
|   |   |-- generate_partner_pdfs.py
|   |   `-- README.md
|   |-- drew-harris-15min-talk-track.md
|   |-- drew-harris-collaboration-spike.md
|   |-- meeting-drew-harris-2026-08-20-debrief.md
|   |-- meeting-drew-harris-2026-08-20-transcript.md
|   |-- overtone-architecture-for-partners.md
|   `-- SAAS.md
|-- marketing/
|   |-- public/
|   |   |-- assets/
|   |   |-- media/
|   |   |   `-- logos/
|   |   |-- apple-touch-icon.png
|   |   |-- favicon.svg
|   |   |-- logo-mark.png
|   |   |-- logo-wordmark.png
|   |   `-- og-image.png
|   |-- src/
|   |   |-- components/
|   |   |   |-- layout/
|   |   |   |   |-- MobileNav.jsx
|   |   |   |   |-- SiteFooter.jsx
|   |   |   |   `-- SiteHeader.jsx
|   |   |   |-- motion/
|   |   |   |   `-- RevealSection.jsx
|   |   |   |-- sections/
|   |   |   |   |-- ComparisonTable.jsx
|   |   |   |   |-- CTABand.jsx
|   |   |   |   |-- FAQAccordion.jsx
|   |   |   |   |-- FeatureGrid.jsx
|   |   |   |   |-- HeroSection.jsx
|   |   |   |   |-- IntegrationStrip.jsx
|   |   |   |   |-- LogoBar.jsx
|   |   |   |   |-- MetricsBand.jsx
|   |   |   |   |-- PricingCards.jsx
|   |   |   |   |-- SplitFeature.jsx
|   |   |   |   |-- StepsTimeline.jsx
|   |   |   |   |-- TestimonialRow.jsx
|   |   |   |   `-- ToneBand.jsx
|   |   |   `-- visuals/
|   |   |       |-- BrandLogo.jsx
|   |   |       |-- DashboardMock.jsx
|   |   |       |-- DeckVoiceMark.jsx
|   |   |       |-- integrations.js
|   |   |       |-- media.js
|   |   |       |-- PlatformLogo.jsx
|   |   |       |-- platforms.js
|   |   |       |-- ScrollReveal.jsx
|   |   |       `-- VisualFrame.jsx
|   |   |-- hooks/
|   |   |   |-- useInView.js
|   |   |   `-- useScrollReveal.js
|   |   |-- pages/
|   |   |   |-- ContactPage.jsx
|   |   |   |-- FeaturesPage.jsx
|   |   |   |-- HomePage.jsx
|   |   |   |-- HowItWorksPage.jsx
|   |   |   |-- PricingPage.jsx
|   |   |   |-- PrivacyPage.jsx
|   |   |   |-- RefundPage.jsx
|   |   |   |-- TermsPage.jsx
|   |   |   `-- UseCasesPage.jsx
|   |   |-- App.jsx
|   |   |-- config.js
|   |   |-- index.css
|   |   |-- Layout.jsx
|   |   |-- legal.js
|   |   `-- main.jsx
|   |-- Dockerfile
|   |-- index.html
|   |-- nginx.conf
|   |-- package.json
|   `-- vite.config.js
|-- presenter/
|   |-- nginx/
|   |   `-- templates/
|   |       `-- default.conf.template
|   |-- public/
|   |   |-- apple-touch-icon.png
|   |   |-- favicon.svg
|   |   `-- logo-mark.png
|   |-- src/
|   |   |-- components/
|   |   |   |-- PresentationStage.jsx
|   |   |   |-- SlideNumber.jsx
|   |   |   |-- SlideViewer.jsx
|   |   |   |-- StatusIndicator.jsx
|   |   |   `-- ToolToasts.jsx
|   |   |-- hooks/
|   |   |   |-- usePresentationTransport.js
|   |   |   |-- useRealtimeAgent.js
|   |   |   |-- useSlideNavigation.js
|   |   |   `-- useWebSocket.js
|   |   |-- utils/
|   |   |   `-- config.js
|   |   |-- App.jsx
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- Dockerfile
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- ARCHITECTURE.md
|-- DEPLOY.md
|-- README.md
|-- skills-lock.json
|-- start-local.ps1
|-- start-local.sh
`-- TESTING.md
```

Local-only files that exist on disk but are not listed here: `backend/.env`, `dashboard/.env`, `presenter/.env`, SQLite DBs under `backend/`, screenshots under `dashboard/.artifacts/`, partner PDFs under `docs/outbound/`, and image assets under `marketing/public/media/`.
