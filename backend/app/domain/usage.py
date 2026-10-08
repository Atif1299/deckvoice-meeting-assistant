from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Session as SessionRow
from app.db.models import SessionState, Subscription, UsageCounter
from app.domain.plans import PlanLimits, limits_for_plan

# Metric keys stored in v2_usage_counters.
METRIC_MINUTES = "meeting_minutes"
METRIC_UPLOADS = "uploads"
METRIC_LAUNCHES = "launches"  # reporting only; not a billing gate

# Session states that occupy a concurrency slot (bot is live and costing money).
LIVE_STATES = (
    SessionState.JOINING.value,
    SessionState.IN_WAITING_ROOM.value,
    SessionState.IN_CALL.value,
    SessionState.RECORDING.value,
)


def _period_month(now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    return ts.strftime("%Y-%m")


def get_active_plan(db: Session, workspace_id: str) -> str:
    sub = (
        db.query(Subscription)
        .filter(Subscription.workspace_id == workspace_id, Subscription.status.in_(["active", "trialing"]))
        .order_by(Subscription.updated_at.desc())
        .first()
    )
    if sub and sub.plan:
        return sub.plan
    return "free"


def plan_limits_for_workspace(db: Session, workspace_id: str) -> PlanLimits:
    return limits_for_plan(get_active_plan(db, workspace_id))


def get_usage(db: Session, workspace_id: str, metric: str) -> int:
    period = _period_month()
    row = (
        db.query(UsageCounter)
        .filter(
            UsageCounter.workspace_id == workspace_id,
            UsageCounter.metric == metric,
            UsageCounter.period_month == period,
        )
        .first()
    )
    return row.count if row else 0


def active_session_count(db: Session, workspace_id: str) -> int:
    return (
        db.query(SessionRow)
        .filter(SessionRow.customer_id == workspace_id, SessionRow.state.in_(LIVE_STATES))
        .count()
    )


def usage_snapshot(db: Session, workspace_id: str) -> dict:
    plan = get_active_plan(db, workspace_id)
    limits = limits_for_plan(plan)
    minutes = get_usage(db, workspace_id, METRIC_MINUTES)
    uploads = get_usage(db, workspace_id, METRIC_UPLOADS)
    launches = get_usage(db, workspace_id, METRIC_LAUNCHES)
    overage_minutes = max(0, minutes - limits.meeting_minutes)
    overage_cost = 0.0
    if overage_minutes and limits.overage_usd_per_hour is not None:
        overage_cost = round(overage_minutes / 60 * limits.overage_usd_per_hour, 2)
    return {
        "plan": plan,
        "plan_label": limits.label,
        "period_month": _period_month(),
        "meeting_minutes": {
            "used": minutes,
            "limit": limits.meeting_minutes,
            "overage": overage_minutes,
            "overage_usd": overage_cost,
            "overage_allowed": limits.allows_overage,
        },
        "uploads": {"used": uploads, "limit": limits.uploads},
        "launches": {"used": launches},
        "concurrency": {
            "active": active_session_count(db, workspace_id),
            "limit": limits.concurrent_sessions,
        },
        "max_session_minutes": limits.max_session_minutes,
    }


def check_upload_quota(db: Session, workspace_id: str) -> None:
    limits = plan_limits_for_workspace(db, workspace_id)
    used = get_usage(db, workspace_id, METRIC_UPLOADS)
    if used >= limits.uploads:
        raise HTTPException(
            status_code=402,
            detail={
                "message": (
                    f"Monthly upload limit reached for the {limits.label} plan "
                    f"({limits.uploads}). Upgrade to continue."
                ),
                "plan": get_active_plan(db, workspace_id),
                "metric": METRIC_UPLOADS,
                "used": used,
                "limit": limits.uploads,
            },
        )


def check_launch_quota(db: Session, workspace_id: str) -> None:
    """Gate a launch on meeting-minutes and concurrency, not launch count."""
    plan = get_active_plan(db, workspace_id)
    limits = limits_for_plan(plan)

    active = active_session_count(db, workspace_id)
    if active >= limits.concurrent_sessions:
        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    f"The {limits.label} plan allows {limits.concurrent_sessions} "
                    f"concurrent meeting(s). End a live session or upgrade."
                ),
                "plan": plan,
                "metric": "concurrent_sessions",
                "used": active,
                "limit": limits.concurrent_sessions,
            },
        )

    used = get_usage(db, workspace_id, METRIC_MINUTES)
    if used >= limits.meeting_minutes and not limits.allows_overage:
        raise HTTPException(
            status_code=402,
            detail={
                "message": (
                    f"Monthly meeting-minute allowance used for the {limits.label} plan "
                    f"({limits.meeting_minutes} min). Upgrade to continue."
                ),
                "plan": plan,
                "metric": METRIC_MINUTES,
                "used": used,
                "limit": limits.meeting_minutes,
            },
        )


def increment_usage(db: Session, workspace_id: str, metric: str, amount: int = 1) -> None:
    if amount <= 0:
        return
    period = _period_month()
    row = (
        db.query(UsageCounter)
        .filter(
            UsageCounter.workspace_id == workspace_id,
            UsageCounter.metric == metric,
            UsageCounter.period_month == period,
        )
        .first()
    )
    if row:
        row.count += amount
    else:
        db.add(
            UsageCounter(
                workspace_id=workspace_id,
                metric=metric,
                period_month=period,
                count=amount,
            )
        )
    db.commit()
