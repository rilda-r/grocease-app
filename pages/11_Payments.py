"""
pages/11_Payments.py
====================
Payments page — view payment obligations, settle payments, remind payers,
and view payment history. Also shows expense split preview from bill scanning.
"""

import os
import sys
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import streamlit as st

from style import apply_base_style
from utils.session import require_auth, get_current_user_id, get_current_room_id, get_current_room_name
from utils.formatting import format_currency, format_datetime, badge_html, safe_error_message
from components.auto_sync import setup_auto_sync
from components.sidebar import render_sidebar, render_room_selector
from components.cards import render_metric_card, render_empty_state
import importlib
import components.payment_table
importlib.reload(components.payment_table)
from components.payment_table import render_payment_table
from components.notifications import render_notification_banner
try:
    from database.database import (
        get_room_payments_live,
        settle_payment_live,
        mark_payment_paid_live,
        confirm_payment_settled_live,
        dispute_payment_live,
        remind_payment_live,
    )
except Exception:
    def get_room_payments_live(room_id):
        return []
    def settle_payment_live(payment_id):
        return False
    def mark_payment_paid_live(payment_id, payer_user_id):
        return {}
    def confirm_payment_settled_live(payment_id, payee_user_id):
        return {}
    def dispute_payment_live(payment_id, payee_user_id):
        return {}
    def remind_payment_live(payment_id, requester_user_id):
        return None
from mock.mock_api import (
    get_payments as mock_get_payments,
    settle_payment as mock_settle_payment,
    remind_payment as mock_remind_payment,
    get_bill,
    get_bill_items,
    calculate_bill_split,
    calculate_equal_split,
    get_room_members,
)
from mock.mock_data import get_username

def get_payments(room_id):
    live = get_room_payments_live(room_id)
    if live:
        return live
    return mock_get_payments(room_id)

def settle_payment(payment_id):
    success = False
    try:
        success = settle_payment_live(payment_id)
    except Exception:
        pass
    if not success:
        mock_settle_payment(payment_id)

def remind_payment(payment_id, requester_user_id):
    """Send a reminder to the payer. Returns {"payer_name": ...}.

    Raises ValueError for rule violations (not the payee / not pending).
    Falls back to the mock store only when the payment is not in the live DB.
    """
    try:
        return remind_payment_live(payment_id, requester_user_id)
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        result = mock_remind_payment(payment_id, requester_user_id)
        if result is None:
            raise ValueError("Only the person who is owed can send a reminder.")
        return result


st.set_page_config(
    page_title="Payments — GrocEase",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_base_style()
require_auth()
render_sidebar()

# ── Select Room Component at top ──────────────────────────────────────────────
col_title, col_sel = st.columns([1.6, 1.1], gap="medium", vertical_alignment="center")
with col_title:
    st.markdown("# 💳 Payments")
with col_sel:
    st.write("")
    render_room_selector(key_prefix="payments_page")

user_id   = get_current_user_id()
room_id   = get_current_room_id()
room_name = get_current_room_name()

# ── Notifications for this user (e.g. "X reminded you to pay") ────────────────
render_notification_banner(user_id, key_prefix="payments_page")

if not room_id:
    render_empty_state("🏠", "No room selected", "Please select a room from the dropdown above to view and settle payments.")
    st.stop()

# ── Real-time Auto-Sync ────────────────────────────────────────────────────────
setup_auto_sync(interval_ms=20000, key="pay_auto_sync")

st.markdown(
    f"""
    <div style="background:#F7FBFA; border:1px solid #CADDD8; border-radius:14px; padding:0.6rem 1rem; margin-bottom:1.2rem;">
        <span style="color:#4A6568; font-size:0.95rem;">Active Room: <strong style="color:#10272A;">{room_name}</strong></span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Expense split preview (from bill scanning flow) ───────────────────────────
split_bill_id = st.session_state.pop("split_bill_id", None)
if split_bill_id:
    bill = get_bill(split_bill_id)
    if bill:
        st.markdown("### 🧾 Expense Split Preview")
        st.markdown(
            f"""
            <div style="background:#F7FBFA; border:1px solid #CADDD8; border-radius:18px;
                        padding:1rem 1.4rem; margin-bottom:1rem; box-shadow:0 4px 20px -2px rgba(16,39,42,0.08);">
                <strong>{bill.get('fileName', 'Bill')}</strong> — Total:
                <span style="font-family:'Fraunces',serif; font-weight:700; color:#0F766E;">
                    {format_currency(float(bill.get('totalAmount', 0.0)))}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        split_tab, equal_tab = st.tabs(["📌 Assigned Split", "⚖️ Equal Split"])

        with split_tab:
            assigned_split = calculate_bill_split(split_bill_id)
            if assigned_split:
                is_shopper = int(bill.get('userId') or bill.get('user_id') or 0) == int(user_id)
                for uid, amt in assigned_split.items():
                    if not (is_shopper or int(uid) == int(user_id)):
                        continue
                    st.markdown(
                        f"""
                        <div style="display:flex; justify-content:space-between;
                                    padding:0.6rem 0.8rem; border-bottom:1px solid #CADDD8;">
                            <div>👤 {get_username(uid)}</div>
                            <div style="font-weight:700; color:#0F766E; font-variant-numeric:tabular-nums;">{format_currency(amt)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No items assigned yet. Go back to Bill Scanning to assign items.")

        with equal_tab:
            try:
                from database.database import get_room_members_with_identities
                db_mems = get_room_members_with_identities(room_id)
                member_ids = [m["user_id"] for m in db_mems] if db_mems else []
            except Exception:
                member_ids = []
            if not member_ids:
                member_ids = [m.get("userId") or m.get("user_id") for m in get_room_members(room_id)]
            equal_split = calculate_equal_split(split_bill_id, member_ids) if member_ids else {}
            if equal_split:
                for uid, amt in equal_split.items():
                    st.markdown(
                        f"""
                        <div style="display:flex; justify-content:space-between;
                                    padding:0.6rem 0.8rem; border-bottom:1px solid #CADDD8;">
                            <div>👤 {get_username(uid)}</div>
                            <div style="font-weight:700; color:#0F766E; font-variant-numeric:tabular-nums;">{format_currency(amt)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No members found in this room to split equally.")

        if st.button("✅ Confirm & Record Payments", type="primary"):
            st.success("Payments recorded! (Mock — no real DB change)")
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

# ── Payment summaries & Strict User Privacy ───────────────────────────────────
all_room_payments = get_payments(room_id)

def _is_payer(p, uid):
    if not isinstance(p, dict) or uid is None:
        return False
    payer = p.get("payerUserId") if p.get("payerUserId") is not None else p.get("payer_user_id")
    if payer is None:
        return False
    try:
        return int(payer) == int(uid)
    except (ValueError, TypeError):
        return str(payer) == str(uid)

def _is_payee(p, uid):
    if not isinstance(p, dict) or uid is None:
        return False
    payee = p.get("payeeUserId") if p.get("payeeUserId") is not None else p.get("payee_user_id")
    if payee is None:
        return False
    try:
        return int(payee) == int(uid)
    except (ValueError, TypeError):
        return str(payee) == str(uid)

def _is_pending(p):
    st_val = str(p.get("paymentStatus") or p.get("payment_status") or "pending").lower()
    return st_val in ("pending", "paid", "awaiting_confirmation")

# STRICT ROOM PRIVACY:
# A user must ONLY see debts and payments where they are the payer OR payee.
# Debts between other roommates in the same room are strictly filtered out.
payments = [
    p for p in all_room_payments
    if _is_payer(p, user_id) or _is_payee(p, user_id)
]

amount_owe = sum(
    float(p.get("amount") or 0.0) for p in payments
    if _is_payer(p, user_id) and (str(p.get("paymentStatus") or p.get("payment_status") or "pending").lower() == "pending")
)
amount_owed_to_me = sum(
    float(p.get("amount") or 0.0) for p in payments
    if _is_payee(p, user_id) and (str(p.get("paymentStatus") or p.get("payment_status") or "pending").lower() == "pending")
)

m1, m2 = st.columns(2)
with m1:
    render_metric_card("I Owe (Pending)", format_currency(amount_owe), accent="danger")
with m2:
    render_metric_card("Owed to Me (Pending)", format_currency(amount_owed_to_me), accent="gold")

st.markdown("<br>", unsafe_allow_html=True)

# ── Filter tabs ───────────────────────────────────────────────────────────────
tab_all, tab_owe, tab_receive, tab_history = st.tabs(
    ["All", "💸 I Owe", "💰 I Receive", "📜 History"]
)

def settle_handler(payment_id):
    try:
        res = mark_payment_paid_live(payment_id, user_id)
        payee = res.get("payee_name", "the payee")
        st.toast(f"Marked as paid! Notification sent to {payee} to confirm. 💸", icon="✅")
    except Exception as exc:
        st.error(f"Could not mark payment as paid: {safe_error_message(exc)}")
    st.rerun()

def confirm_handler(payment_id):
    try:
        res = confirm_payment_settled_live(payment_id, user_id)
        payer = res.get("payer_name", "the payer")
        st.toast(f"Settlement confirmed! Payment from {payer} resolved. 🎉", icon="✅")
    except Exception as exc:
        st.error(f"Could not confirm settlement: {safe_error_message(exc)}")
    st.rerun()

def dispute_handler(payment_id):
    try:
        dispute_payment_live(payment_id, user_id)
        st.toast("Reported as not received. Status reset to pending. ⚠️", icon="⚠️")
    except Exception as exc:
        st.error(f"Could not dispute payment: {safe_error_message(exc)}")
    st.rerun()

def remind_handler(payment_id):
    try:
        result = remind_payment(payment_id, user_id)
        payer = result.get("payer_name", "Member") if isinstance(result, dict) else "Member"
        st.toast(f"Reminder sent to {payer}.", icon="🔔")
    except ValueError as e:
        st.warning(str(e))
    except Exception as e:
        st.error(f"Could not send reminder: {safe_error_message(e)}")

def _is_active_debt(p):
    st_val = (p.get("paymentStatus") or p.get("payment_status") or "pending").lower()
    return st_val in ("pending", "paid", "awaiting_confirmation")

with tab_all:
    try:
        render_payment_table(
            payments,
            user_id,
            on_settle=settle_handler,
            on_confirm=confirm_handler,
            on_dispute=dispute_handler,
            on_remind=remind_handler,
            key_prefix="all",
        )
    except Exception as exc:
        st.error(f"Could not render payments: {safe_error_message(exc)}")

with tab_owe:
    try:
        owe_list = [p for p in payments if _is_payer(p, user_id) and _is_active_debt(p)]
        render_payment_table(
            owe_list,
            user_id,
            on_settle=settle_handler,
            key_prefix="owe",
        )
    except Exception as exc:
        st.error(f"Could not render owed debts: {safe_error_message(exc)}")

with tab_receive:
    try:
        receive_list = [p for p in payments if _is_payee(p, user_id) and _is_active_debt(p)]
        render_payment_table(
            receive_list,
            user_id,
            on_confirm=confirm_handler,
            on_dispute=dispute_handler,
            on_remind=remind_handler,
            key_prefix="recv",
        )
    except Exception as exc:
        st.error(f"Could not render receivable debts: {safe_error_message(exc)}")

with tab_history:
    try:
        history = [p for p in payments if (p.get("paymentStatus") or p.get("payment_status")) in ("settled", "reported")]
        render_payment_table(history, user_id, key_prefix="hist")
    except Exception as exc:
        st.error(f"Could not render payment history: {safe_error_message(exc)}")
