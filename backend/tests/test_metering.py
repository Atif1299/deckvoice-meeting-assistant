from __future__ import annotations

import time

import pytest
from fastapi import HTTPException

from app.db import SessionLocal, create_tables
from app.db.models import Session as SessionRow
from app.db.models import SessionState, Subscription, UsageCounter
from app.domain.metering import (
    close_billing_window,
    elapsed_minutes,
    on_status_change,
    open_billing_window,
    overrunning_sessions,
)
from app.domain.session_store import LiveSession, store
from app.domain.usage import (
    METRIC_MINUTES,
    METRIC_UPLOADS,
    active_session_count,
    check_launch_quota,
    check_upload_quota,
    get_usage,
    increment_usage,
    usage_snapshot,
)
from app.meetings.recall import RecallClient


def _reset(workspace_id: str) -> None:
    create_tables()
    db = SessionLocal()
    try:
        db.query(UsageCounter).filter(UsageCounter.workspace_id == workspace_id).delete()
        db.query(Subscription).filter(Subscription.workspace_id == workspace_id).delete()
        db.query(SessionRow).filter(SessionRow.customer_id == workspace_id).delete()
        db.commit()
    finally:
        db.close()


def _set_plan(workspace_id: str, plan: str) -> None:
    db = SessionLocal()
    try:
        db.add(Subscription(workspace_id=workspace_id, plan=plan, status="active"))
        db.commit()
    finally:
        db.close()


def _make_session(session_id: str, workspace_id: str | None, state: str) -> LiveSession:
    sess = LiveSession(
        session_id=session_id,
        presentation_id="pres-1",
        bot_name="DeckVoice",
        meeting_url="https://meet.google.com/abc-defg-hij",
        customer_id=workspace_id,
        recall_bot_id=f"bot-{session_id}",
        state=state,
        extra={},
    )
    store.create(sess)
    return sess


# --- metering lifecycle ----------------------------------------------------


def test_billing_window_opens_once_and_bills_elapsed_minutes():
    ws = "ws_meter_basic"
    _reset(ws)
    _set_plan(ws, "team")
    _make_session("sess-meter-1", ws, SessionState.RECORDING.value)

    open_billing_window("sess-meter-1")
    started = (store.get("sess-meter-1").extra or {}).get("billing_started_at")
    assert started is not None

    # A second open must not reset the clock.
    open_billing_window("sess-meter-1")
    assert (store.get("sess-meter-1").extra or {}).get("billing_started_at") == started

    minutes = close_billing_window("sess-meter-1")
    assert minutes == 1  # partial minutes round up to a billable minute

    db = SessionLocal()
    try:
        assert get_usage(db, ws, METRIC_MINUTES) == 1
    finally:
        db.close()


def test_closing_twice_does_not_double_bill():
    ws = "ws_meter_idempotent"
    _reset(ws)
    _set_plan(ws, "team")
    _make_session("sess-meter-2", ws, SessionState.RECORDING.value)

    open_billing_window("sess-meter-2")
    first = close_billing_window("sess-meter-2")
    second = close_billing_window("sess-meter-2")

    assert first == second
    db = SessionLocal()
    try:
        assert get_usage(db, ws, METRIC_MINUTES) == first
    finally:
        db.close()


def test_bot_that_never_joined_bills_nothing():
    ws = "ws_meter_nojoin"
    _reset(ws)
    _set_plan(ws, "team")
    _make_session("sess-meter-3", ws, SessionState.JOINING.value)

    # Straight to a terminal state without ever entering the call.
    assert close_billing_window("sess-meter-3") == 0
    db = SessionLocal()
    try:
        assert get_usage(db, ws, METRIC_MINUTES) == 0
    finally:
        db.close()


def test_closed_window_cannot_be_reopened_by_a_late_status_event():
    ws = "ws_meter_late"
    _reset(ws)
    _set_plan(ws, "team")
    _make_session("sess-meter-4", ws, SessionState.RECORDING.value)

    open_billing_window("sess-meter-4")
    close_billing_window("sess-meter-4")
    on_status_change("sess-meter-4", SessionState.RECORDING.value)

    assert (store.get("sess-meter-4").extra or {}).get("billing_closed") is True
    db = SessionLocal()
    try:
        assert get_usage(db, ws, METRIC_MINUTES) == 1
    finally:
        db.close()


def test_status_transitions_drive_the_meter():
    ws = "ws_meter_status"
    _reset(ws)
    _set_plan(ws, "team")
    _make_session("sess-meter-5", ws, SessionState.JOINING.value)

    on_status_change("sess-meter-5", SessionState.IN_CALL.value)
    assert (store.get("sess-meter-5").extra or {}).get("billing_started_at")

    on_status_change("sess-meter-5", SessionState.CALL_ENDED.value)
    assert (store.get("sess-meter-5").extra or {}).get("billing_closed") is True


def test_elapsed_minutes_tracks_a_running_session():
    ws = "ws_meter_elapsed"
    _reset(ws)
    _set_plan(ws, "team")
    _make_session("sess-meter-6", ws, SessionState.RECORDING.value)
    # 4m50s — partial minutes round up, so this bills as 5.
    store.merge_extra("sess-meter-6", billing_started_at=time.time() - 290)
    assert elapsed_minutes("sess-meter-6") == 5


# --- quota gating ----------------------------------------------------------


def test_launch_blocked_when_minutes_exhausted_without_overage():
    ws = "ws_quota_minutes"
    _reset(ws)
    _set_plan(ws, "free")
    db = SessionLocal()
    try:
        increment_usage(db, ws, METRIC_MINUTES, 30)  # free allowance is 30
        with pytest.raises(HTTPException) as exc:
            check_launch_quota(db, ws)
        assert exc.value.status_code == 402
        assert exc.value.detail["metric"] == METRIC_MINUTES
    finally:
        db.close()


def test_launch_allowed_past_allowance_when_plan_permits_overage():
    ws = "ws_quota_overage"
    _reset(ws)
    _set_plan(ws, "team")
    db = SessionLocal()
    try:
        increment_usage(db, ws, METRIC_MINUTES, 700)  # team allowance is 600
        check_launch_quota(db, ws)  # must not raise
    finally:
        db.close()


def test_launch_blocked_when_concurrency_limit_reached():
    ws = "ws_quota_concurrent"
    _reset(ws)
    _set_plan(ws, "free")  # 1 concurrent session
    _make_session("sess-conc-1", ws, SessionState.RECORDING.value)

    db = SessionLocal()
    try:
        assert active_session_count(db, ws) == 1
        with pytest.raises(HTTPException) as exc:
            check_launch_quota(db, ws)
        assert exc.value.status_code == 409
        assert exc.value.detail["metric"] == "concurrent_sessions"
    finally:
        db.close()


def test_ended_sessions_release_their_concurrency_slot():
    ws = "ws_quota_release"
    _reset(ws)
    _set_plan(ws, "free")
    _make_session("sess-conc-2", ws, SessionState.RECORDING.value)
    store.update("sess-conc-2", state=SessionState.CALL_ENDED.value)

    db = SessionLocal()
    try:
        assert active_session_count(db, ws) == 0
        check_launch_quota(db, ws)  # must not raise
    finally:
        db.close()


def test_upload_quota_enforced_per_plan():
    ws = "ws_quota_uploads"
    _reset(ws)
    _set_plan(ws, "free")  # 2 uploads
    db = SessionLocal()
    try:
        increment_usage(db, ws, METRIC_UPLOADS, 2)
        with pytest.raises(HTTPException) as exc:
            check_upload_quota(db, ws)
        assert exc.value.status_code == 402
    finally:
        db.close()


# --- overrun watchdog ------------------------------------------------------


def test_watchdog_flags_a_session_past_its_plan_ceiling():
    ws = "ws_overrun"
    _reset(ws)
    _set_plan(ws, "free")  # 20 minute ceiling
    _make_session("sess-overrun-1", ws, SessionState.RECORDING.value)
    store.merge_extra("sess-overrun-1", billing_started_at=time.time() - 25 * 60)

    flagged = {s for s, _bot, _m, _cap in overrunning_sessions()}
    assert "sess-overrun-1" in flagged


def test_watchdog_ignores_a_session_within_its_ceiling():
    ws = "ws_within"
    _reset(ws)
    _set_plan(ws, "business")  # 180 minute ceiling
    _make_session("sess-within-1", ws, SessionState.RECORDING.value)
    store.merge_extra("sess-within-1", billing_started_at=time.time() - 30 * 60)

    flagged = {s for s, _bot, _m, _cap in overrunning_sessions()}
    assert "sess-within-1" not in flagged


# --- Recall cost guards ----------------------------------------------------


def test_bot_payload_carries_a_hard_recording_timeout():
    payload = RecallClient().build_create_bot_payload(
        meeting_url="https://meet.google.com/abc-defg-hij",
        bot_name="DeckVoice",
        output_media_page_url="https://presenter.example/?session=x",
        max_session_minutes=90,
    )
    leave = payload["automatic_leave"]
    assert leave["in_call_recording_timeout"] == 90 * 60
    assert leave["everyone_left_timeout"] > 0
    assert leave["noone_joined_timeout"] > 0
    assert leave["silence_detection"]["timeout"] > 0


def test_recording_timeout_never_collapses_to_zero():
    leave = RecallClient().build_automatic_leave(max_session_minutes=0)
    assert leave["in_call_recording_timeout"] >= 60


# --- usage snapshot --------------------------------------------------------


def test_usage_snapshot_reports_overage_cost():
    ws = "ws_snapshot"
    _reset(ws)
    _set_plan(ws, "team")  # 600 min included, $12/hr overage
    db = SessionLocal()
    try:
        increment_usage(db, ws, METRIC_MINUTES, 660)
        snap = usage_snapshot(db, ws)
        assert snap["plan"] == "team"
        assert snap["meeting_minutes"]["used"] == 660
        assert snap["meeting_minutes"]["overage"] == 60
        assert snap["meeting_minutes"]["overage_usd"] == 12.0
        assert snap["concurrency"]["limit"] == 3
        assert snap["max_session_minutes"] == 90
    finally:
        db.close()


def test_usage_snapshot_defaults_to_free_without_subscription():
    ws = "ws_snapshot_free"
    _reset(ws)
    db = SessionLocal()
    try:
        snap = usage_snapshot(db, ws)
        assert snap["plan"] == "free"
        assert snap["meeting_minutes"]["limit"] == 30
        assert snap["meeting_minutes"]["overage_allowed"] is False
    finally:
        db.close()
