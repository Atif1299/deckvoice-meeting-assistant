from __future__ import annotations

from dataclasses import dataclass

# Billing is metered on meeting-minutes, not launches. A "launch" is unbounded
# cost: the Recall bot plus the realtime audio model both bill for as long as
# the bot sits in the call, so launch counts cannot protect margin.
#
# COGS is roughly Recall bot-hours + realtime speech-to-speech in both
# directions. Included minutes and overage rates below are set so every tier
# stays gross-margin positive at the included allowance and on overage.


@dataclass(frozen=True)
class PlanLimits:
    label: str
    price_usd: int
    # Included meeting-minutes per billing month.
    meeting_minutes: int
    # Deck uploads per billing month.
    uploads: int
    # Bots this workspace may have in meetings at the same time.
    concurrent_sessions: int
    # Hard per-session ceiling. Enforced by the watchdog and mirrored into the
    # Recall bot's automatic_leave config so cost is capped even if our
    # watchdog process dies.
    max_session_minutes: int
    # None means a hard stop at the included allowance (no overage billing).
    overage_usd_per_hour: float | None = None

    @property
    def allows_overage(self) -> bool:
        return self.overage_usd_per_hour is not None

    @property
    def included_hours(self) -> float:
        return round(self.meeting_minutes / 60, 1)


# Current catalogue.
FREE = PlanLimits(
    label="Free",
    price_usd=0,
    meeting_minutes=30,
    uploads=2,
    concurrent_sessions=1,
    max_session_minutes=20,
    overage_usd_per_hour=None,
)

TEAM = PlanLimits(
    label="Team",
    price_usd=99,
    meeting_minutes=600,
    uploads=25,
    concurrent_sessions=3,
    max_session_minutes=90,
    overage_usd_per_hour=12.0,
)

BUSINESS = PlanLimits(
    label="Business",
    price_usd=399,
    meeting_minutes=3000,
    uploads=200,
    concurrent_sessions=10,
    max_session_minutes=180,
    overage_usd_per_hour=10.0,
)

ENTERPRISE = PlanLimits(
    label="Enterprise",
    price_usd=0,  # contract-priced
    meeting_minutes=12000,
    uploads=1000,
    concurrent_sessions=40,
    max_session_minutes=240,
    overage_usd_per_hour=8.0,
)

# Grandfathered tiers. Existing $10/$20 subscribers keep working, but on
# minute allowances that are not loss-making, until they are migrated.
LEGACY_STARTER = PlanLimits(
    label="Starter (legacy)",
    price_usd=10,
    meeting_minutes=120,
    uploads=3,
    concurrent_sessions=1,
    max_session_minutes=60,
    overage_usd_per_hour=None,
)

LEGACY_PRO = PlanLimits(
    label="Pro (legacy)",
    price_usd=20,
    meeting_minutes=300,
    uploads=10,
    concurrent_sessions=2,
    max_session_minutes=90,
    overage_usd_per_hour=None,
)

# Internal operator accounts bypass quota entirely; kept here so the watchdog
# still has a session ceiling to enforce.
OPERATOR = PlanLimits(
    label="Operator",
    price_usd=0,
    meeting_minutes=100000,
    uploads=100000,
    concurrent_sessions=100,
    max_session_minutes=240,
    overage_usd_per_hour=None,
)


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": FREE,
    "team": TEAM,
    "business": BUSINESS,
    "enterprise": ENTERPRISE,
    "starter": LEGACY_STARTER,
    "pro": LEGACY_PRO,
    "operator": OPERATOR,
}

# Plans that can be bought self-serve through Paddle checkout.
SELF_SERVE_PLANS = ("team", "business")

# Plans that exist only for subscribers who bought before the repricing.
LEGACY_PLANS = ("starter", "pro")


def limits_for_plan(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get((plan or "").lower(), FREE)


def is_legacy_plan(plan: str) -> bool:
    return (plan or "").lower() in LEGACY_PLANS
