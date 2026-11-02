"""
pages/08_Grocery_List.py
========================
Grocery list page — view, add, edit, and delete items in the current room.
"""

import sys
import os
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import streamlit as st

from style import apply_base_style
from utils.session import require_auth, get_current_user_id, get_current_room_id, get_current_room_name
from utils.formatting import badge_html, safe_error_message
from components.auto_sync import setup_auto_sync
from components.sidebar import render_sidebar, render_room_selector
from components.help_guide import render_help_button
from components.cards import render_empty_state
from components.alerts import permission_error
from components.grocery_table import render_grocery_table
from components.forms import render_add_grocery_form
from database.database import (
    get_live_grocery_items,
    add_live_grocery_item,
    increment_grocery_item_quantity,
    update_live_grocery_item,
    delete_live_grocery_item,
)
from mock.mock_api import (
    get_grocery_items as mock_get_grocery_items,
    add_grocery_item as mock_add_grocery_item,
    increment_grocery_item_quantity as mock_increment_qty,
    update_grocery_item as mock_update_grocery_item,
    delete_grocery_item as mock_delete_grocery_item,
)

st.set_page_config(
    page_title="Grocery List — GrocEase",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_base_style()
require_auth()
render_sidebar()

col_title, col_help, col_sel = st.columns([1.5, 0.35, 1.15], gap="small", vertical_alignment="center")
with col_title:
    st.markdown("# 🛒 Grocery List")
with col_help:
    render_help_button(
        page_title="Grocery List",
        tip="Plan and organize household items to buy before going shopping.",
        items=[
            ("➕ Add Item", "Add a new grocery item with quantity, units, priority, and category."),
            ("✏️ Edit", "Update an item's quantity or details right in place."),
            ("🗑️ Delete", "Remove an item from this room's grocery list."),
            ("🏠 Active Room", "Switch between your shared grocery groups."),
            ("🧺 Go to Shopping", "Switch to live in-store mode to check items off into your cart."),
            ("🔄 Sync", "Syncs live additions and edits made by other roommates immediately."),
        ],
        key="grocery_list",
    )
with col_sel:
    st.write("")
    render_room_selector(key_prefix="grocery_page")

user_id   = get_current_user_id()
room_id   = get_current_room_id()
room_name = get_current_room_name()

# ── Room guard ────────────────────────────────────────────────────────────────
if not room_id:
    render_empty_state(
        "🏠",
        "No room selected",
        "Select or join a room from above to start your grocery list.",
    )
    if st.button("Go to Rooms", type="primary"):
        st.switch_page("pages/07_Rooms.py")
    st.stop()

# ── Real-time Auto-Sync across all roommates ─────────────────────────────────
setup_auto_sync(
    interval_ms=3500,
    key="gl_auto_sync",
    pause=bool(st.session_state.get("edit_item_id") or st.session_state.get("duplicate_confirm")),
)

# Room sub-header with live status indicator
st.markdown(
    f"<p style='color:#4A6568; margin-top:-0.5rem;'>"
    f"Viewing items in: <strong>{room_name}</strong> &nbsp;"
    f"<span style='background:#EAF1EB; color:#6B8F71; border:1px solid #6B8F71; padding:2px 8px; border-radius:12px; font-size:0.76rem; font-weight:700;'>"
    f"🟢 Live Auto-Sync</span></p>",
    unsafe_allow_html=True,
)

st.markdown("<hr style='border:none; border-top:1px solid #CADDD8; margin:0.2rem 0 1.2rem 0;'>", unsafe_allow_html=True)


# ── Helper to fetch room items from Supabase ──────────────────────────────────
def fetch_room_items(rid: int) -> list:
    try:
        return get_live_grocery_items(rid) or []
    except Exception:
        return []


all_items = fetch_room_items(room_id)

# ── Duplicate check state & dialog ────────────────────────────────────────────
if "duplicate_confirm" not in st.session_state:
    st.session_state["duplicate_confirm"] = None


def apply_add_quantity(existing_id: int, add_qty: int, item_name: str):
    """Increments quantity upon an existing duplicate item in Supabase."""
    try:
        increment_grocery_item_quantity(existing_id, add_qty)
    except Exception:
        pass
    st.success(f"✅ Added +{add_qty} to **{item_name}**!")


# Dialog for duplicate item confirmation
if hasattr(st, "dialog"):
    @st.dialog("Item Already Exists")
    def show_duplicate_dialog(dup_info):
        st.warning("⚠️ **This item already exists. Do you want to add quantity upon it?**")
        st.markdown(
            f"- **Item:** `{dup_info['existing_name']}`\n"
            f"- **Current Quantity:** ×{dup_info['existing_qty']}\n"
            f"- **Adding:** +{dup_info['add_qty']}\n"
            f"- **New Total:** ×{dup_info['existing_qty'] + dup_info['add_qty']}"
        )
        c_yes, c_sep, c_no = st.columns(3)
        with c_yes:
            if st.button("➕ Add to Quantity", type="primary", use_container_width=True):
                apply_add_quantity(dup_info["existing_id"], dup_info["add_qty"], dup_info["existing_name"])
                st.session_state["duplicate_confirm"] = None
                st.rerun()
        with c_sep:
            if st.button("➕ Separate Row", use_container_width=True):
                try:
                    add_live_grocery_item(room_id, user_id, dup_info["existing_name"], dup_info["add_qty"])
                except Exception:
                    pass
                st.session_state["duplicate_confirm"] = None
                st.rerun()
        with c_no:
            if st.button("Cancel", use_container_width=True):
                st.session_state["duplicate_confirm"] = None
                st.rerun()


# Also render an in-page modal banner as fallback
if st.session_state.get("duplicate_confirm"):
    dup = st.session_state["duplicate_confirm"]
    with st.container():
        st.markdown(
            """
            <div style="background:#FFF9E6; border:1px solid #E6D080; border-radius:8px; padding:1.2rem; margin-bottom:1rem;">
                <h4 style="margin:0 0 0.5rem 0; color:#856404;">⚠️ Duplicate Item Detected</h4>
                <p style="margin:0 0 0.8rem 0; color:#333;">
                    <strong>This item already exists. Do you want to add quantity upon it?</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_dup_y, col_dup_sep, col_dup_n = st.columns(3)
        with col_dup_y:
            if st.button(f"➕ Add to Quantity", type="primary", key="dup_inpage_yes"):
                apply_add_quantity(dup["existing_id"], dup["add_qty"], dup["existing_name"])
                st.session_state["duplicate_confirm"] = None
                st.rerun()
        with col_dup_sep:
            if st.button("➕ Add as Separate Row", key="dup_inpage_sep"):
                try:
                    add_live_grocery_item(room_id, user_id, dup["existing_name"], dup["add_qty"])
                except Exception:
                    pass
                st.session_state["duplicate_confirm"] = None
                st.rerun()
        with col_dup_n:
            if st.button("Cancel", key="dup_inpage_cancel"):
                st.session_state["duplicate_confirm"] = None
                st.rerun()

    # Trigger native dialog if available
    if hasattr(st, "dialog"):
        show_duplicate_dialog(dup)


# ── Status filter ─────────────────────────────────────────────────────────────
status_filter = st.radio(
    "Filter by status",
    options=["All", "Pending", "Purchased", "Unavailable"],
    horizontal=True,
    key="grocery_status_filter",
)

# ── Add item form ─────────────────────────────────────────────────────────────
new_item = render_add_grocery_form(room_id, key_prefix="gl_")
if new_item:
    item_name_clean = new_item["itemName"].strip()
    # Check for duplicate item in active list (case-insensitive) ONLY for current user's own items!
    # If another user added the same item, keep them completely separate (1 row per user).
    def _is_my_item(i):
        u = i.get("userId") if i.get("userId") is not None else i.get("user_id")
        return u is not None and int(u) == int(user_id)

    existing_dup = next(
        (
            i for i in all_items
            if _is_my_item(i)
            and i.get("status") == "pending"
            and (i.get("itemName") or i.get("item_name", "")).strip().lower() == item_name_clean.lower()
        ),
        None,
    )
    if existing_dup:
        st.session_state["duplicate_confirm"] = {
            "existing_id": existing_dup["id"],
            "existing_name": existing_dup.get("itemName") or existing_dup.get("item_name", item_name_clean),
            "existing_qty": existing_dup.get("quantity", 1),
            "add_qty": new_item["quantity"],
        }
        st.rerun()
    else:
        # Save to Supabase
        try:
            add_live_grocery_item(room_id, user_id, item_name_clean, new_item["quantity"])
            st.success(f"✅ Added **{item_name_clean}** ×{new_item['quantity']}")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add item: {safe_error_message(exc)}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Edit state ────────────────────────────────────────────────────────────────
if "edit_item_id" not in st.session_state:
    st.session_state["edit_item_id"] = None


def handle_edit(item):
    if item.get("status") == "purchased":
        st.error("🔒 Purchased items are locked and cannot be edited.")
        return
    st.session_state["edit_item_id"] = item["id"]
    st.session_state["edit_item_name_val"] = item["itemName"]
    st.session_state["edit_item_qty_val"]  = item["quantity"]
    st.rerun()


def handle_delete(item_id):
    # Protect purchased items from deletion
    target = next((i for i in all_items if i["id"] == item_id), None)
    if target and target.get("status") == "purchased":
        st.error("🔒 Purchased items are locked to protect purchase logs and cannot be deleted.")
        return
    try:
        delete_live_grocery_item(item_id)
    except Exception:
        pass
    try:
        mock_delete_grocery_item(item_id)
    except Exception:
        pass
    st.success("Item deleted.")
    st.rerun()


# ── Inline edit form ──────────────────────────────────────────────────────────
if st.session_state["edit_item_id"] is not None:
    edit_id = st.session_state["edit_item_id"]
    st.markdown("#### ✏️ Edit Item")
    with st.form("edit_grocery_form"):
        col_n, col_q = st.columns([3, 1])
        with col_n:
            new_name = st.text_input("Item name", value=st.session_state.get("edit_item_name_val", ""))
        with col_q:
            new_qty = st.number_input("Qty", min_value=1, max_value=999,
                                       value=st.session_state.get("edit_item_qty_val", 1), step=1)
        save_col, cancel_col = st.columns(2)
        with save_col:
            if st.form_submit_button("Save", type="primary"):
                if new_name.strip():
                    try:
                        update_live_grocery_item(edit_id, new_name.strip(), int(new_qty))
                    except Exception:
                        pass
                    try:
                        mock_update_grocery_item(edit_id, new_name.strip(), int(new_qty))
                    except Exception:
                        pass
                    st.session_state["edit_item_id"] = None
                    st.success("Item updated.")
                    st.rerun()
        with cancel_col:
            if st.form_submit_button("Cancel"):
                st.session_state["edit_item_id"] = None
                st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# ── Items table with live data ───────────────────────────────────────────────
items = fetch_room_items(room_id)
all_items = list(items)

if status_filter != "All":
    filter_val = status_filter.lower()
    items = [i for i in items if i["status"] == filter_val]

# Summary counts
counts = {
    "pending":     sum(1 for i in all_items if i["status"] == "pending"),
    "purchased":   sum(1 for i in all_items if i["status"] == "purchased"),
    "unavailable": sum(1 for i in all_items if i["status"] == "unavailable"),
}
sc1, sc2, sc3 = st.columns(3)
sc1.markdown(badge_html("pending") + f"&nbsp; **{counts['pending']}** pending", unsafe_allow_html=True)
sc2.markdown(badge_html("purchased") + f"&nbsp; **{counts['purchased']}** purchased", unsafe_allow_html=True)
sc3.markdown(badge_html("unavailable") + f"&nbsp; **{counts['unavailable']}** unavailable", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

render_grocery_table(items, user_id, on_edit=handle_edit, on_delete=handle_delete)

# ── Start Shopping button ─────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if counts["pending"] > 0:
    if st.button("🧺 Start Shopping", type="primary"):
        st.session_state["shopping_mode"] = True
        st.switch_page("pages/09_Shopping.py")

