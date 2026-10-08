from __future__ import annotations

import asyncio
import logging
import math
import time

from app.db import SessionLocal
from app.db.models import Session as SessionRow
from app.db.models import SessionState
from app.domain.plans import limits_for_plan
from app.domain.session_store import store
from app.domain.usage import (
    LIVE_STATES,
    METRIC_MINUTES,
    get_active_plan,
    increment_usage,
)

logger = logging.getLogger("deckvoice.v2.metering")

# Bot is in the meeting and billing from these states onward.
BILLABLE_STATES = (
    SessionState.IN_CALL.value,
    SessionState.RECORDING.value,
)

# States that mean the bot is gone and the meter must be closed.
TERMINAL_STATES = (
    SessionState.CALL_ENDED.value,
    SessionState.DONE.value,
    SessionState.FATAL.value,
)


def open_billing_window(session_id: str) -> None:
    """Start the meter the first time a bot is actually in the meeting."""
    sess = store.get(session_id)
    if not sess:
        return
    extra = sess.extra or {}
    if extra.get("billing_started_at") or extra.get("billing_closed"):
        return
    store.merge_extra(session_id, billing_started_at=time.time())
    logger.info("billing window opened session_id=%s", session_id)


def elapsed_minutes(session_id: str) -> int:
    sess = store.get(session_id)
    if not sess:
        return 0
    started = (sess.extra or {}).get("billing_started_at")
    if not started:
        return 0
    return max(1, math.ceil((time.time() - float(started)) / 60))


def close_billing_window(session_id: str) -> int:
    """Bill the elapsed meeting-minutes exactly once. Returns minutes billed."""
    sess = store.get(session_id)
    if not sess:
        return 0
    extra = sess.extra or {}
    if extra.get("billing_closed"):
        return int(extra.get("billed_minutes") or 0)
    started = extra.get("billing_started_at")
    if not started:
        # Bot never made it into the call — nothing to bill, but close the
        # window so a later status event cannot reopen it.
        store.merge_extra(session_id, billing_closed=True, billed_minutes=0)
        return 0

    minutes = max(1, math.ceil((time.time() - float(started)) / 60))
    store.merge_extra(session_id, billing_closed=True, billed_minutes=minutes)

    workspace_id = sess.customer_id
    if not workspace_id:
        # Operator/demo session — metered on the session row only.
        logger.info("billing closed (untenanted) session_id=%s minutes=%s", session_id, minutes)
        return minutes

    db = SessionLocal()
    try:
        increment_usage(db, workspace_id, METRIC_MINUTES, minutes)
    finally:
        db.close()
    logger.info(
        "billing closed session_id=%s workspace_id=%s minutes=%s",
        session_id,
        workspace_id,
        minutes,
    )
    return minutes


def on_status_change(session_id: str, state: str) -> None:
    """Drive the meter from Recall bot status transitions."""
    if state in BILLABLE_STATES:
        open_billing_window(session_id)
    elif state in TERMINAL_STATES:
        close_billing_window(session_id)


def max_session_minutes_for(workspace_id: str | None) -> int:
    if not workspace_id:
        return limits_for_plan("operator").max_session_minutes
    db = SessionLocal()
    try:
        return limits_for_plan(get_active_plan(db, workspace_id)).max_session_minutes
    finally:
        db.close()


def overrunning_sessions() -> list[tuple[str, str | None, int, int]]:
    """Live sessions past their plan's per-session ceiling.

    Returns (session_id, recall_bot_id, elapsed_minutes, cap_minutes).
    """
    db = SessionLocal()
    try:
        rows = db.query(SessionRow).filter(SessionRow.state.in_(LIVE_STATES)).all()
        candidates = [(r.session_id, r.recall_bot_id, r.customer_id) for r in rows]
    finally:
        db.close()

    over: list[tuple[str, str | None, int, int]] = []
    for session_id, recall_bot_id, workspace_id in candidates:
        sess = store.get(session_id)
        if not sess:
            continue
        extra = sess.extra or {}
        if extra.get("billing_closed"):
            continue
        started = extra.get("billing_started_at")
        if not started:
            continue
        minutes = math.ceil((time.time() - float(started)) / 60)
        cap = max_session_minutes_for(workspace_id)
        if minutes >= cap:
            over.append((session_id, recall_bot_id, minutes, cap))
    return over


async def enforce_session_caps() -> int:
    """Force-leave any bot that has run past its plan ceiling. Returns count."""
    from app.meetings.recall import RecallClient

    stopped = 0
    for session_id, recall_bot_id, minutes, cap in overrunning_sessions():
        logger.warning(
            "session over cap session_id=%s minutes=%s cap=%s — forcing leave",
            session_id,
            minutes,
            cap,
        )
        if recall_bot_id:
            try:
                await RecallClient().leave_call(recall_bot_id)
            except Exception:  # noqa: BLE001
                logger.exception("force leave failed session_id=%s", session_id)
        close_billing_window(session_id)
        store.update(session_id, state=SessionState.CALL_ENDED.value)
        stopped += 1
    return stopped


async def watchdog_loop(interval_seconds: int) -> None:
    """Periodic guard so a stuck bot cannot bill indefinitely."""
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await enforce_session_caps()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("session watchdog iteration failed")
