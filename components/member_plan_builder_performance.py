from __future__ import annotations

import copy

import streamlit as st

from components import profile_builder_source_contract as source_contract
from components import recommendation_profile_store as profile_store


_INSTALLED = False
_ORIGINAL_BUILD_SOURCE_CONTRACT = source_contract.build_profile_builder_source_contract
_ORIGINAL_LOAD_PROFILE_SOURCES = profile_store.load_profile_builder_sources


@st.cache_data(ttl=300, show_spinner=False)
def _cached_source_contract():
    return _ORIGINAL_BUILD_SOURCE_CONTRACT()


@st.cache_data(ttl=180, show_spinner=False)
def _cached_profile_sources():
    return _ORIGINAL_LOAD_PROFILE_SOURCES()


def _build_source_contract_cached():
    # Page-level Streamlit functions are recreated on rerun, so layout patches still
    # need to execute even when repository data comes from cache.
    source_contract.patch_streamlit_source_instruction_fields()
    source_contract.patch_profile_builder_source_detail_layout()
    sources, snapshots, message = _cached_source_contract()
    return copy.deepcopy(sources), copy.deepcopy(snapshots), message


def _load_profile_sources_cached():
    sources, message = _cached_profile_sources()
    return copy.deepcopy(sources), message


def install_member_plan_builder_performance_cache() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    source_contract.build_profile_builder_source_contract = _build_source_contract_cached
    profile_store.load_profile_builder_sources = _load_profile_sources_cached
    _INSTALLED = True


def clear_member_plan_builder_source_caches() -> None:
    _cached_source_contract.clear()
    _cached_profile_sources.clear()
