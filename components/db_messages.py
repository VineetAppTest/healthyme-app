"""Message database facade.

v61 cleanup foundation: imports existing stable functions from db.py.
No business logic changed yet; this prepares safe future split.
"""
from components.db import (
    get_member_messages,
    get_member_unread_messages,
    get_member_archived_messages,
    mark_member_message_read,
)
