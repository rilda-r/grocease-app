import os
import secrets
import sys

from config.settings import get_settings
from database.connection import (
    DatabaseError,
    get_connection,
    init_schema,
)

_TABLES_DROP_ORDER = (
    "payments",
    "bill_items",
    "bills",
    "budgets",
    "personal_expenses",
    "grocery_items",
    "room_members",
    "rooms",
    "users",
)


def prepare_test_database() -> str:
    """Point the process at a ``*_test`` database, create it and wipe all data.

    Refuses to touch any database whose name does not end in ``_test``,
    and explicitly refuses to wipe live Supabase databases.
    """
    cfg = get_settings()
    if cfg.db_url and ("supabase" in cfg.db_url.lower() or "pooler" in cfg.db_url.lower()):
        # Safety guard: Never truncate live Supabase database!
        return "supabase_protected"

    name = cfg.db_name
    if not name.endswith("_test"):
        name = f"{name}_test"
        os.environ["GROCEASE_DB_NAME"] = name
    init_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        tables_csv = ", ".join(_TABLES_DROP_ORDER)
        try:
            cur.execute(f"TRUNCATE TABLE {tables_csv} CASCADE")
        except Exception:
            for table in _TABLES_DROP_ORDER:
                try:
                    cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                except Exception:
                    pass
        conn.commit()
        cur.close()
    return name


TEST_PASSWORD = "Str0ng#Pass"


def database_available_for_tests() -> bool:
    try:
        cfg = get_settings()
        if cfg.db_url and ("supabase" in cfg.db_url.lower() or "pooler" in cfg.db_url.lower()):
            # Live Supabase is protected; do not run destructive DB unit tests against it
            return False
        with get_connection():
            return True
    except Exception:
        return False


def make_test_user(name: str) -> int:
    from security.password_hash import hash_password
    from database.database import create_user, get_user_by_email, mark_verified
    email = f"{name}_{secrets.token_hex(4)}@test.grocease.local"
    pw = hash_password(TEST_PASSWORD)
    create_user(name, email, pw)
    u = get_user_by_email(email)
    mark_verified(email)
    return u["id"]


def make_test_room(creator_id: int, *member_ids: int) -> dict:
    from services.room_service import create_room, join_room
    res = create_room(creator_id, f"Room {secrets.token_hex(3)}")
    room = res["data"]
    for mid in member_ids:
        join_room(mid, room["code"])
    return room
