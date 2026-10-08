from __future__ import annotations

from app.domain.plans import (
    LEGACY_PLANS,
    PLAN_LIMITS,
    SELF_SERVE_PLANS,
    is_legacy_plan,
    limits_for_plan,
)


def test_current_catalogue_limits():
    free = limits_for_plan("free")
    assert free.meeting_minutes == 30
    assert free.uploads == 2
    assert free.concurrent_sessions == 1
    assert free.max_session_minutes == 20
    assert free.allows_overage is False

    team = limits_for_plan("team")
    assert team.price_usd == 99
    assert team.meeting_minutes == 600
    assert team.allows_overage is True

    business = limits_for_plan("business")
    assert business.price_usd == 399
    assert business.meeting_minutes == 3000
    assert business.concurrent_sessions == 10


def test_unknown_plan_falls_back_to_free():
    assert limits_for_plan("nonsense").label == "Free"
    assert limits_for_plan("").label == "Free"


def test_every_plan_has_a_hard_session_ceiling():
    """No plan may allow an unbounded bot — that is the cost leak we closed."""
    for name, limits in PLAN_LIMITS.items():
        assert limits.max_session_minutes > 0, name
        assert limits.max_session_minutes <= 240, name


def test_paid_tiers_price_above_included_cost_floor():
    """Included minutes must not be sold below a conservative COGS floor.

    Assumes ~$3.00/hour blended for the Recall bot plus realtime audio in both
    directions. If a tier ever violates this, it loses money on every customer
    who uses their full allowance.
    """
    cogs_per_hour = 3.00
    for name in SELF_SERVE_PLANS:
        limits = PLAN_LIMITS[name]
        included_cost = limits.included_hours * cogs_per_hour
        assert included_cost < limits.price_usd, (
            f"{name}: included allowance costs ${included_cost:.2f} "
            f"but sells for ${limits.price_usd}"
        )


def test_overage_rate_is_above_marginal_cost():
    cogs_per_hour = 3.00
    for name in SELF_SERVE_PLANS:
        limits = PLAN_LIMITS[name]
        assert limits.overage_usd_per_hour is not None, name
        assert limits.overage_usd_per_hour > cogs_per_hour, name


def test_free_tier_is_strictly_below_every_paid_tier():
    """The old catalogue gave Free and Starter the same allowance."""
    free = limits_for_plan("free")
    for name in SELF_SERVE_PLANS:
        paid = PLAN_LIMITS[name]
        assert paid.meeting_minutes > free.meeting_minutes, name
        assert paid.uploads > free.uploads, name


def test_plans_form_an_ascending_ladder():
    ladder = [PLAN_LIMITS[name] for name in SELF_SERVE_PLANS]
    minutes = [p.meeting_minutes for p in ladder]
    prices = [p.price_usd for p in ladder]
    assert minutes == sorted(minutes)
    assert prices == sorted(prices)


def test_legacy_plans_flagged_and_not_self_serve():
    for name in LEGACY_PLANS:
        assert is_legacy_plan(name)
        assert name not in SELF_SERVE_PLANS
    assert not is_legacy_plan("team")


def test_legacy_plans_capped_below_their_old_allowance():
    """Grandfathered $10/$20 subscribers keep access on sane minute caps."""
    starter = limits_for_plan("starter")
    pro = limits_for_plan("pro")
    assert starter.meeting_minutes == 120
    assert pro.meeting_minutes == 300
    assert starter.allows_overage is False
    assert pro.allows_overage is False
