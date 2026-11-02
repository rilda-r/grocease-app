"""
components/expense_table.py
===========================
Personal expense list component.
Minimalistic, responsive card design for seamless mobile & desktop views.
"""

import streamlit as st
from utils.formatting import format_currency, format_date, badge_html


def render_expense_table(expenses: list, on_delete=None):
    """
    Render personal expenses in a clean, responsive card layout.
    """
    if not expenses:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1.5px dashed #CADDD8; border-radius:18px;
                        text-align:center; padding:2.5rem 1rem; color:#4A6568; box-shadow:0 2px 8px rgba(16,39,42,0.03);">
                <div style="font-size:2.8rem; margin-bottom:0.4rem;">📝</div>
                <div style="font-family:'Fraunces',Georgia,serif; font-size:1.1rem; font-weight:700; color:#10272A;">No expenses found</div>
                <div style="font-size:0.88rem; color:#4A6568; margin-top:0.3rem;">Add your first expense using the form above.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<div style='font-size:0.85rem; font-weight:700; color:#4A6568; margin-bottom:0.6rem; text-transform:uppercase; letter-spacing:0.05em;'>"
        f"Recorded Expenses ({len(expenses)})"
        f"</div>",
        unsafe_allow_html=True,
    )

    for exp in sorted(expenses, key=lambda e: str(e.get("expenseDate") or e.get("expense_date") or ""), reverse=True):
        exp_id = exp.get("id")
        amt = float(exp.get("amount", 0.0))
        cat = (exp.get("category") or "General").capitalize()
        desc = exp.get("description") or "—"
        dt = format_date(exp.get("expenseDate") or exp.get("expense_date"))

        with st.container(border=True):
            col_main, col_right = st.columns([3.5, 1.5], vertical_alignment="center")
            with col_main:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span style="font-size:1.02rem; font-weight:700; color:#10272A;">📝 {cat}</span>
                        {badge_html(cat.lower())}
                    </div>
                    <div style="font-size:0.82rem; color:#4A6568; margin-top:3px;">
                        <span>{desc}</span> &nbsp;•&nbsp; <span style="color:#0F766E; font-weight:600;">📅 {dt}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_right:
                col_amt, col_del = st.columns([2.5, 1], vertical_alignment="center")
                with col_amt:
                    st.markdown(
                        f"<div style='font-size:1.05rem; font-weight:800; color:#0F766E; text-align:right;'>{format_currency(amt)}</div>",
                        unsafe_allow_html=True,
                    )
                with col_del:
                    if on_delete and st.button("🗑️", key=f"del_exp_{exp_id}", help="Delete expense", use_container_width=True):
                        on_delete(exp_id)
