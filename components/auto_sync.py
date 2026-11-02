"""
components/auto_sync.py
=======================
Real-time automatic background synchronization for shared room activities.
Periodically triggers a lightweight background refresh so when any roommate
makes changes (adds/deletes items, marks bought, settles payments),
all other roommates' screens automatically update in real time.
"""

import streamlit as st


def setup_auto_sync(interval_ms: int = 3500, key: str = "room_auto_sync", pause: bool = False):
    """
    Trigger automatic background synchronization.
    If pause=True (e.g. while editing an item or filling an input),
    auto-sync is temporarily halted to prevent interrupting the user.
    """
    if pause:
        return
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=interval_ms, key=key)
    except Exception:
        pass
