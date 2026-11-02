"""
components/grocery_table.py
===========================
Grocery list table component.
Minimalistic, responsive card design for seamless mobile & desktop views.
"""

import streamlit as st
from utils.formatting import badge_html
from mock.mock_data import get_username


def render_grocery_table(
    items: list,
    current_user_id: int,
    on_edit=None,
    on_delete=None,
):
    """
    Render grocery items in a clean, responsive card layout.
    """
    if not items:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1.5px dashed #CADDD8; border-radius:18px;
                        text-align:center; padding:2.5rem 1rem; color:#4A6568; box-shadow:0 2px 8px rgba(16,39,42,0.03);">
                <div style="font-size:2.8rem; margin-bottom:0.4rem;">🛒</div>
                <div style="font-family:'Fraunces',Georgia,serif; font-size:1.1rem; font-weight:700; color:#10272A;">No items yet</div>
                <div style="font-size:0.88rem; color:#4A6568; margin-top:0.3rem;">Add your first grocery item using the form above.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<div style='font-size:0.85rem; font-weight:700; color:#4A6568; margin-bottom:0.6rem; text-transform:uppercase; letter-spacing:0.05em;'>"
        f"Items in list ({len(items)})"
        f"</div>",
        unsafe_allow_html=True,
    )

    for item in items:
        item_id = item["id"]
        item_name = item.get("itemName") or item.get("item_name", "Item")
        qty = item.get("quantity", 1)
        user_uid = item.get("userId") if item.get("userId") is not None else item.get("user_id")
        added_by_display = item.get("addedByName") or item.get("added_by_name") or get_username(user_uid)
        status = item.get("status", "pending")

        is_owner = user_uid is not None and int(user_uid) == int(current_user_id)
        is_purchased = status == "purchased"

        with st.container(border=True):
            col_info, col_actions = st.columns([4, 1.2], vertical_alignment="center")
            with col_info:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span style="font-size:1.05rem; font-weight:700; color:#10272A;">🛒 {item_name}</span>
                        <span style="background:#E6F4F1; color:#0F766E; font-weight:700; font-size:0.82rem; padding:2px 8px; border-radius:10px;">×{qty}</span>
                        {badge_html(status)}
                    </div>
                    <div style="font-size:0.8rem; color:#4A6568; margin-top:3px;">
                        👤 Added by <strong style="color:#10272A;">{added_by_display}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_actions:
                if is_purchased:
                    st.markdown("<div style='text-align:right; font-size:0.8rem; color:#4A6568;'>🔒 Purchased</div>", unsafe_allow_html=True)
                elif is_owner:
                    c_edit, c_del = st.columns(2)
                    with c_edit:
                        if on_edit and st.button("✏️", key=f"edit_item_{item_id}", help="Edit item", use_container_width=True):
                            on_edit(item)
                    with c_del:
                        if on_delete and st.button("🗑️", key=f"del_item_{item_id}", help="Delete item", use_container_width=True):
                            on_delete(item_id)
                else:
                    st.write("")
