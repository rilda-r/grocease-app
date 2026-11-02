"""
components/payment_table.py
===========================
Payment records table component.
Shared Kitchen Counter aesthetic design.
"""

import streamlit as st
from utils.formatting import format_currency, format_datetime, badge_html
from mock.mock_data import get_username


def render_payment_table(
    payments: list,
    current_user_id: int,
    on_settle=None,
    on_remind=None,
    on_report=None,
    key_prefix: str = "",
):
    """
    Render payment records.

    Args:
        payments: list of Payment dicts
        current_user_id: logged-in user id
        on_settle: callback(payment_id)
        on_remind: callback(payment_id) - shown only to the person who is owed
        on_report: optional callback(payment_id) for backward-compatibility
        key_prefix: unique prefix for widget keys
    """
    if not payments:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1.5px dashed #CADDD8; border-radius:18px;
                        text-align:center; padding:2.5rem 1rem; color:#4A6568; box-shadow:0 2px 8px rgba(16,39,42,0.03);">
                <div style="font-size:2.8rem; margin-bottom:0.4rem;">💳</div>
                <div style="font-family:'Fraunces',Georgia,serif; font-size:1.1rem; font-weight:700; color:#10272A;">No payments yet</div>
                <div style="font-size:0.88rem; color:#4A6568; margin-top:0.3rem;">Payments appear after a bill is split in your rooms.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    headers = ["Payer", "Payee", "Amount", "Status", "Date", "Actions"]
    header_cols = st.columns([2, 2, 2, 2, 3, 2])
    for col, h in zip(header_cols, headers):
        col.markdown(f"<span style='font-size:0.82rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:#9A6A12;'>{h}</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:0.4rem 0 0.8rem 0; border:none; border-top:1.5px solid #CADDD8;'>", unsafe_allow_html=True)

    for p in payments:
        row = st.columns([2, 2, 2, 2, 3, 2])
        payer_id = p.get("payerUserId") if p.get("payerUserId") is not None else p.get("payer_user_id")
        payee_id = p.get("payeeUserId") if p.get("payeeUserId") is not None else p.get("payee_user_id")

        payer_disp = p.get("payerName") or get_username(payer_id)
        payee_disp = p.get("payeeName") or get_username(payee_id)
        amount_val = float(p.get("amount", 0.0))
        status = p.get("paymentStatus") or p.get("payment_status", "pending")
        created_val = p.get("createdAt") or p.get("created_at", "")

        row[0].write(payer_disp)
        row[1].write(payee_disp)
        row[2].markdown(f"<span class='money-tabular'>{format_currency(amount_val)}</span>", unsafe_allow_html=True)
        row[3].markdown(badge_html(status), unsafe_allow_html=True)
        row[4].write(format_datetime(created_val))

        with row[5]:
            if status == "pending":
                # Payer can settle; only the person who is owed (the shopper) can remind
                if payer_id is not None and int(payer_id) == int(current_user_id) and on_settle:
                    if st.button("✅ Settle", key=f"{key_prefix}_settle_{p['id']}"):
                        on_settle(p["id"])
                if payee_id is not None and int(payee_id) == int(current_user_id) and on_remind:
                    if st.button("🔔 Remind", key=f"{key_prefix}_remind_{p['id']}"):
                        on_remind(p["id"])
                if on_report and (payer_id is not None and int(payer_id) == int(current_user_id)):
                    if st.button("⚠️ Report", key=f"{key_prefix}_report_{p['id']}"):
                        on_report(p["id"])
            else:
                st.write("—")
