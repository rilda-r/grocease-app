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
    notifications = get_unread_notifications(user_id)
    if not notifications:
        return

    for n in notifications:
        col_msg, col_btn = st.columns([5, 1], vertical_alignment="center")
        with col_msg:
            st.markdown(
                f"""
                <div style="background:#FFF8E8; border:1px solid #E3C680; border-left:4px solid #E3A02E;
                            border-radius:12px; padding:0.6rem 0.9rem;">
                    <span style="color:#10272A; font-size:0.95rem;">🔔 {n['message']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("Dismiss", key=f"{key_prefix}_notif_{n['id']}", use_container_width=True):
                try:
                    mark_notification_read(n["id"], user_id)
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
