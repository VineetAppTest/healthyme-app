from __future__ import annotations

import functools
import inspect
import pathlib
import sys
from typing import Any

import pandas as pd
import streamlit as st

from components.exercise_repository import EXERCISE_COLUMNS, list_exercise_repository


_MARKER = "_hm_exercise_repository_runtime_v1"
_LEGACY_SUFFIX = "/data/exercises.csv"
_MEMBER_PAGE_SUFFIX = "pages/09_Exercise_Repository.py"


def _is_exercise_csv(value: Any) -> bool:
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


def _exercise_dataframe() -> pd.DataFrame:
    rows = list_exercise_repository(active_only=False)
    data = [{column: row.get(column, "") for column in EXERCISE_COLUMNS} for row in rows]
    frame = pd.DataFrame(data, columns=EXERCISE_COLUMNS)
    if rows:
        frame.index = [str(row.get("id", index)) for index, row in enumerate(rows)]
    return frame


def install_exercise_repository_runtime() -> None:
    current_read_csv = pd.read_csv
    if getattr(current_read_csv, _MARKER, False):
        return

    @functools.wraps(current_read_csv)
    def repository_backed_read_csv(filepath_or_buffer, *args, **kwargs):
        if _is_exercise_csv(filepath_or_buffer):
            return _exercise_dataframe()
        return current_read_csv(filepath_or_buffer, *args, **kwargs)

    setattr(repository_backed_read_csv, _MARKER, True)
    pd.read_csv = repository_backed_read_csv

    current_cache_data = st.cache_data

    @functools.wraps(current_cache_data)
    def exercise_repository_cache_policy(func=None, *args, **kwargs):
        target_page = _stack_contains(_MEMBER_PAGE_SUFFIX)
        if target_page:
            if callable(func):
                return func

            def identity_decorator(wrapped):
                return wrapped

            return identity_decorator
        return current_cache_data(func, *args, **kwargs)

    setattr(exercise_repository_cache_policy, _MARKER, True)
    for attribute in ("clear",):
        if hasattr(current_cache_data, attribute):
            setattr(exercise_repository_cache_policy, attribute, getattr(current_cache_data, attribute))
    st.cache_data = exercise_repository_cache_policy

    import components.recommendation_contract as recommendation_contract

    original_list_repository_items = recommendation_contract.list_repository_items
    if not getattr(original_list_repository_items, _MARKER, False):

        @functools.wraps(original_list_repository_items)
        def persistent_list_repository_items(resource_type: str, active_only: bool = True):
            resource_text = str(resource_type or "").strip().lower()
            if resource_text in {"exercise", "exercises", "workout", "workouts"}:
                return list_exercise_repository(active_only=active_only)
            return original_list_repository_items(resource_type, active_only=active_only)

        setattr(persistent_list_repository_items, _MARKER, True)
        recommendation_contract.list_repository_items = persistent_list_repository_items

        source_contract = sys.modules.get("components.profile_builder_source_contract")
        if source_contract is not None:
            source_contract.list_repository_items = persistent_list_repository_items
