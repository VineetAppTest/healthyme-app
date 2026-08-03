from __future__ import annotations

from functools import wraps
from typing import Any, Dict, List, Tuple

import components.profile_builder_module_store as _module_store
from components.meal_profile_builder_phase_b import (
    MEAL_EDITABLE_ITEM_TYPES,
    is_meal_profile_builder_editable_type,
)


_INSTALL_MARKER = "_healthyme_meal_profile_builder_phase_b_boundary"


def install_meal_profile_builder_write_boundary() -> None:
    """Make the live builder fail closed for non-meal module saves.

    Historical Exercise and Supplement rows remain in the profile item table and
    continue to load for Preview/Publish. This wrapper only prevents the Meal
    Profile Builder runtime from replacing those item types.
    """
    current = _module_store.save_profile_module
    if getattr(current, _INSTALL_MARKER, False):
        return

    @wraps(current)
    def meals_only_save(
        profile_id: str,
        member_id: str,
        item_type: str,
        items: List[Dict[str, Any]],
        *,
        created_by_user_id: str = "",
        created_by_email: str = "",
    ) -> Tuple[bool, str]:
        if not is_meal_profile_builder_editable_type(item_type):
            return (
                False,
                "Meal Profile Builder can save Meal rows only. Exercise and Supplement allocation are managed through independent workflows.",
            )
        return current(
            profile_id,
            member_id,
            item_type,
            items,
            created_by_user_id=created_by_user_id,
            created_by_email=created_by_email,
        )

    setattr(meals_only_save, _INSTALL_MARKER, True)
    _module_store.save_profile_module = meals_only_save
    _module_store.VALID_MODULES = set(MEAL_EDITABLE_ITEM_TYPES)
