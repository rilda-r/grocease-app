"""
components/notifications.py
===========================
In-app notification banner (e.g. "Rilda reminded you to pay ₹120.00 ...").

Usage:
    from components.notifications import render_notification_banner
    render_notification_banner(user_id, key_prefix="payments_page")
"""

import streamlit as st

from database.database import (
    get_unread_notifications,
    mark_notification_read,
    mark_all_notifications_read,
)


def render_notification_banner(user_id: int, key_prefix: str = "global") -> None:
    """Show the user's unread notifications with a Dismiss button on each."""
    if not user_id:
        return

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
                    mark_notification_read(notif_id, user_id)
                except Exception:
                    pass
                st.rerun()

    if len(notifications) > 1:
        if st.button("Dismiss all", key=f"{key_prefix}_notif_all"):
            try:
                mark_all_notifications_read(user_id)
            except Exception:
                pass
            st.rerun()

    st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)
