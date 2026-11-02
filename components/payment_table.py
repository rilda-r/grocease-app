"""
components/payment_table.py
===========================
Payment records component.
Minimalistic, single-line card design for seamless mobile & desktop views.
Resilient against arbitrary keyword arguments, unexpected types, and nulls.
"""

import streamlit as st
from utils.formatting import format_currency, format_datetime, badge_html
from mock.mock_data import get_username


def render_payment_table(*args, **kwargs):
    """
    Render payment records in a clean, single-line horizontal card layout.
    Accepts arbitrary positional and keyword arguments safely to prevent any signature TypeError.
    """
    # 1. Positional / Keyword Argument Unpacking
    payments = args[0] if len(args) > 0 else kwargs.get("payments", [])
    current_user_id = args[1] if len(args) > 1 else kwargs.get("current_user_id", kwargs.get("user_id"))

    on_settle = kwargs.get("on_settle")
    on_confirm = kwargs.get("on_confirm")
    on_dispute = kwargs.get("on_dispute")
    on_remind = kwargs.get("on_remind")
    on_report = kwargs.get("on_report")
    key_prefix = kwargs.get("key_prefix", "")

    # Ensure payments is an iterable list
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

    try:
        payment_list = list(payments)
    except Exception:
        payment_list = []

    st.markdown(
        f"<div style='font-size:0.85rem; font-weight:700; color:#4A6568; margin-bottom:0.6rem; text-transform:uppercase; letter-spacing:0.05em;'>"
        f"Payment Records ({len(payment_list)})"
        f"</div>",
        unsafe_allow_html=True,
    )

    for p in payment_list:
        if not isinstance(p, dict):
            continue

        try:
            p_id = p.get("id", 0)
            payer_id = p.get("payerUserId") if p.get("payerUserId") is not None else p.get("payer_user_id")
            payee_id = p.get("payeeUserId") if p.get("payeeUserId") is not None else p.get("payee_user_id")

            try:
                payer_disp = p.get("payerName") or (get_username(payer_id) if payer_id is not None else "Member")
            except Exception:
                payer_disp = "Member"

            try:
                payee_disp = p.get("payeeName") or (get_username(payee_id) if payee_id is not None else "Member")
            except Exception:
                payee_disp = "Member"

            try:
                amount_val = float(p.get("amount") or 0.0)
            except Exception:
                amount_val = 0.0

            status = str(p.get("paymentStatus") or p.get("payment_status") or "pending").lower()
            created_val = str(p.get("createdAt") or p.get("created_at") or "")

            is_payer = False
            if payer_id is not None and current_user_id is not None:
                try:
                    is_payer = int(payer_id) == int(current_user_id)
                except Exception:
                    is_payer = str(payer_id) == str(current_user_id)

            is_payee = False
            if payee_id is not None and current_user_id is not None:
                try:
                    is_payee = int(payee_id) == int(current_user_id)
                except Exception:
                    is_payee = str(payee_id) == str(current_user_id)

            st.markdown('<div class="groc-card-row">', unsafe_allow_html=True)
            with st.container(border=True):
                col_info, col_amt, col_action = st.columns([3.2, 1.4, 1.4], vertical_alignment="center")
                with col_info:
                    st.markdown(
                        f"""
                        <div class="groc-item-inline" style="display:flex; align-items:center; gap:6px; flex-wrap:nowrap; overflow:hidden; min-width:0;">
                            <span style="font-size:0.92rem; font-weight:700; color:#10272A; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">👤 {payer_disp} ➔ {payee_disp}</span>
                            <span style="font-size:0.72rem; color:#4A6568; white-space:nowrap; flex-shrink:0;">📅 {format_datetime(created_val)}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_amt:
                    st.markdown(
                        f"<div style='font-size:0.95rem; font-weight:800; color:#0F766E; text-align:right; white-space:nowrap;'>{format_currency(amount_val)} {badge_html(status)}</div>",
                        unsafe_allow_html=True,
                    )

                with col_action:
                    if status == "pending":
                        if is_payer and on_settle:
                            if st.button("💸 Settle", key=f"{key_prefix}_settle_{p_id}", use_container_width=True, help="Mark payment as sent"):
                                on_settle(p_id)
                        elif is_payee and on_remind:
                            if st.button("🔔 Remind", key=f"{key_prefix}_remind_{p_id}", use_container_width=True, help="Send payment reminder"):
                                on_remind(p_id)
                        elif on_report and is_payer:
                            if st.button("⚠️ Report", key=f"{key_prefix}_report_{p_id}", use_container_width=True):
                                on_report(p_id)
                        else:
                            st.markdown("<div style='text-align:right; font-size:0.82rem; color:#E3A02E; font-weight:600;'>Pending</div>", unsafe_allow_html=True)
                    elif status in ("paid", "awaiting_confirmation"):
                        if is_payee:
                            if on_confirm and st.button("✅ Confirm", key=f"{key_prefix}_confirm_{p_id}", type="primary", use_container_width=True, help="Confirm money received in your account"):
                                on_confirm(p_id)
                        elif is_payer:
                            st.markdown("<div style='text-align:right; font-size:0.82rem; color:#0F766E; font-weight:600; white-space:nowrap;'>⏳ Awaiting Confirm</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='text-align:right; font-size:0.82rem; color:#0F766E; font-weight:600;'>Paid</div>", unsafe_allow_html=True)
                    elif status == "settled":
                        st.markdown("<div style='text-align:right; font-size:0.82rem; color:#6B8F71; font-weight:700;'>✅ Settled</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align:right; font-size:0.82rem; color:#6B8F71; font-weight:600;'>{status.capitalize()}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            continue
