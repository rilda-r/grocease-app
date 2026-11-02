"""
components/notifications.py
===========================
In-app notification banner (e.g. "Rilda reminded you to pay ₹120.00 ...").

Usage:
    from components.notifications import render_notification_banner
    render_notification_banner(user_id, key_prefix="payments_page")
"""

import os
import sys
import streamlit as st

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# Safe fallback imports so importing this module never raises an ImportError
try:
    from database.database import (
        get_unread_notifications,
        mark_notification_read,
        mark_all_notifications_read,
    )
except Exception:
    def get_unread_notifications(user_id: int, limit: int = 20) -> list:
        return []

    def mark_notification_read(notification_id: int, user_id: int) -> bool:
        return False

    def mark_all_notifications_read(user_id: int) -> bool:
        return False


def render_notification_banner(user_id: int, key_prefix: str = "global") -> None:
    """Show the user's unread notifications with a Dismiss button on each."""
    if not user_id:
        return

    try:
        from database.database import get_unread_notifications as _fetch_notifs
        notifications = _fetch_notifs(user_id)
    except Exception:
        try:
            notifications = get_unread_notifications(user_id)
        except Exception:
            notifications = []

    if not notifications:
        return

    for n in notifications:
        col_msg, col_btn = st.columns([5, 1])
        with col_msg:
            msg = n.get("message", "")
            st.markdown(
                f"""
                <div style="background:#FFF8E8; border:1px solid #E3C680; border-left:4px solid #E3A02E;
                            border-radius:12px; padding:0.6rem 0.9rem;">
                    <span style="color:#10272A; font-size:0.95rem;">🔔 {msg}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            notif_id = n.get("id")
            if st.button("Dismiss", key=f"{key_prefix}_notif_{notif_id}", use_container_width=True):
                try:
                    from database.database import mark_notification_read as _mark_read
                    _mark_read(notif_id, user_id)
                except Exception:
                    try:
                        mark_notification_read(notif_id, user_id)
                    except Exception:
                        pass
                st.rerun()

    if len(notifications) > 1:
        if st.button("Dismiss all", key=f"{key_prefix}_notif_all"):
            try:
                from database.database import mark_all_notifications_read as _mark_all_read
                _mark_all_read(user_id)
            except Exception:
                try:
                    mark_all_notifications_read(user_id)
                except Exception:
                    pass
            st.rerun()

    st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)
