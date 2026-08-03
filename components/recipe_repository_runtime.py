from __future__ import annotations

import functools
import inspect
import pathlib
import sys
from typing import Any

import pandas as pd
import streamlit as st

from components.recipe_repository import RECIPE_COLUMNS, list_recipe_repository


_MARKER = "_hm_recipe_repository_runtime_v1"
_LEGACY_SUFFIX = "/data/recipes.csv"
_MEMBER_PAGE_SUFFIX = "pages/08_Recipe_Repository.py"


def _is_recipe_csv(value: Any) -> bool:
    if not isinstance(value, (str, pathlib.Path)):
        return False
    text = str(value).replace("\\", "/")
    return text.endswith(_LEGACY_SUFFIX)


def _stack_contains(suffix: str) -> bool:
    for frame_info in inspect.stack():
        page_file = str(frame_info.frame.f_globals.get("__file__") or "").replace("\\", "/")
        if page_file.endswith(suffix):
            return True
    return False


def _recipe_dataframe() -> pd.DataFrame:
    rows = list_recipe_repository(active_only=False)
    data = [{column: row.get(column, "") for column in RECIPE_COLUMNS} for row in rows]
    frame = pd.DataFrame(data, columns=RECIPE_COLUMNS)
    if rows:
        identities = []
        for index, row in enumerate(rows):
            source_id = str(row.get("id", index)).strip()
            identities.append(int(source_id) if source_id.isdigit() else source_id)
        frame.index = identities
    return frame


def install_recipe_repository_runtime() -> None:
    current_read_csv = pd.read_csv
    if getattr(current_read_csv, _MARKER, False):
        return

    @functools.wraps(current_read_csv)
    def repository_backed_read_csv(filepath_or_buffer, *args, **kwargs):
        if _is_recipe_csv(filepath_or_buffer):
            return _recipe_dataframe()
        return current_read_csv(filepath_or_buffer, *args, **kwargs)

    setattr(repository_backed_read_csv, _MARKER, True)
    pd.read_csv = repository_backed_read_csv

    current_cache_data = st.cache_data

    @functools.wraps(current_cache_data)
    def recipe_repository_cache_policy(func=None, *args, **kwargs):
        target_page = _stack_contains(_MEMBER_PAGE_SUFFIX)
        if target_page:
            if callable(func):
                return func

            def identity_decorator(wrapped):
                return wrapped

            return identity_decorator
        return current_cache_data(func, *args, **kwargs)

    setattr(recipe_repository_cache_policy, _MARKER, True)
    for attribute in ("clear",):
        if hasattr(current_cache_data, attribute):
            setattr(recipe_repository_cache_policy, attribute, getattr(current_cache_data, attribute))
    st.cache_data = recipe_repository_cache_policy

    import components.recommendation_contract as recommendation_contract

    original_list_repository_items = recommendation_contract.list_repository_items
    if not getattr(original_list_repository_items, _MARKER, False):

        @functools.wraps(original_list_repository_items)
        def canonical_list_repository_items(resource_type: str, active_only: bool = True):
            resource_text = str(resource_type or "").strip().lower()
            if resource_text in {"recipe", "recipes", "meal", "meals"}:
                return list_recipe_repository(active_only=active_only)
            return original_list_repository_items(resource_type, active_only=active_only)

        setattr(canonical_list_repository_items, _MARKER, True)
        recommendation_contract.list_repository_items = canonical_list_repository_items

        source_contract = sys.modules.get("components.profile_builder_source_contract")
        if source_contract is not None:
            source_contract.list_repository_items = canonical_list_repository_items

    original_sync_repository_to_state = recommendation_contract.sync_repository_to_state
    if not getattr(original_sync_repository_to_state, _MARKER, False):

        @functools.wraps(original_sync_repository_to_state)
        def canonical_sync_repository_to_state(resource_type: str):
            resource_text = str(resource_type or "").strip().lower()
            if resource_text in {"recipe", "recipes", "meal", "meals"}:
                # Compatibility call retained as a read-only snapshot. Canonical Recipe
                # rows must never be mirrored back into app-state as a second authority.
                return list_recipe_repository(active_only=False)
            return original_sync_repository_to_state(resource_type)

        setattr(canonical_sync_repository_to_state, _MARKER, True)
        recommendation_contract.sync_repository_to_state = canonical_sync_repository_to_state
