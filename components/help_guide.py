"""
components/help_guide.py
========================
Help and navigation guidance component.
Provides a compact '❓' popover button with 1-line explanations for every button
and workflow tips to guide users smoothly through the app.
"""

import streamlit as st


def render_help_button(page_title: str, items: list, tip: str = None, key: str = None):
    """
    Render a minimalist '❓' help popover button.
    items: list of tuples (button_or_action_label, one_line_explanation)
    """
    btn_key = f"help_{key}" if key else None
    with st.popover("❓", help=f"How to use {page_title}"):
        st.markdown(
            f"""
            <div style="font-family:'Fraunces',Georgia,serif; font-size:1.05rem; font-weight:700; color:#10272A; margin-bottom:0.25rem;">
                💡 {page_title} Guide
            </div>
            """,
            unsafe_allow_html=True,
        )
        if tip:
            st.markdown(
                f"""
                <div style="font-size:0.82rem; color:#4A6568; background:#F5FAF8; border-left:3px solid #0F766E; padding:0.4rem 0.6rem; border-radius:6px; margin-bottom:0.6rem; line-height:1.4;">
                    {tip}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("<hr style='margin:0.2rem 0 0.5rem 0; border:none; border-top:1px solid #CADDD8;'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:#4A6568; margin-bottom:0.45rem;'>Buttons & Actions:</div>",
            unsafe_allow_html=True,
        )
        for label, desc in items:
            st.markdown(
                f"""
                <div style="margin-bottom:0.5rem; font-size:0.83rem; line-height:1.35;">
                    <strong style="color:#0F766E; background:#E6F4F1; padding:1px 7px; border-radius:6px; font-size:0.8rem; display:inline-block; margin-bottom:2px;">{label}</strong>
                    <div style="color:#2C3E40; font-size:0.82rem;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
