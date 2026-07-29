from __future__ import annotations

import copy
import functools
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable

import streamlit as st


PROFILE_CACHE_TTL_SECONDS = 60
_PROFILE_PATCH_MARKER = "_hm_admin_profile_performance_v1"
_PACKAGE_PATCH_MARKER = "_hm_admin_package_performance_v1"
_SCHEDULING_PATCH_MARKER = "_hm_admin_scheduling_performance_v1"
_SCHEDULING_REQUEST_CACHE: ContextVar[dict[tuple[Any, ...], Any] | None] = ContextVar(
    "hm_admin_scheduling_request_cache",
    default=None,
)


def _cached_read(function: Callable[..., Any]) -> Callable[..., Any]:
    return st.cache_data(
        ttl=PROFILE_CACHE_TTL_SECONDS,
        show_spinner=False,
    )(function)


def install_profile_builder_performance() -> None:
    """Cache stable Profile Builder reads without changing save or publish behavior."""

    import components.profile_builder_source_contract as source_contract
    import components.recommendation_profile_store as profile_store

    if not getattr(source_contract, _PROFILE_PATCH_MARKER, False):
        original_builder = source_contract.build_profile_builder_source_contract
        cached_builder = _cached_read(original_builder)

        @functools.wraps(original_builder)
        def build_profile_builder_source_contract_cached():
            result = cached_builder()
            # These patches are page-context dependent and must still run on every rerun.
            source_contract.patch_streamlit_source_instruction_fields()
            source_contract.patch_profile_builder_source_detail_layout()
            return result

        source_contract.build_profile_builder_source_contract = (
            build_profile_builder_source_contract_cached
        )
        setattr(source_contract, _PROFILE_PATCH_MARKER, True)

    if not getattr(profile_store, _PROFILE_PATCH_MARKER, False):
        original_status = profile_store.check_profile_builder_store
        original_snapshot_status = profile_store.profile_source_snapshot_columns_ready
        original_sources = profile_store.load_profile_builder_sources

        cached_status = _cached_read(original_status)
        cached_snapshot_status = _cached_read(original_snapshot_status)
        cached_sources = _cached_read(original_sources)

        @functools.wraps(original_status)
        def check_profile_builder_store_cached():
            return cached_status()

        @functools.wraps(original_snapshot_status)
        def profile_source_snapshot_columns_ready_cached():
            return cached_snapshot_status()

        @functools.wraps(original_sources)
        def load_profile_builder_sources_cached():
            return cached_sources()

        profile_store.check_profile_builder_store = check_profile_builder_store_cached
        profile_store.profile_source_snapshot_columns_ready = (
            profile_source_snapshot_columns_ready_cached
        )
        profile_store.load_profile_builder_sources = load_profile_builder_sources_cached
        setattr(profile_store, _PROFILE_PATCH_MARKER, True)


class LazySubscriptionMetrics(Mapping[str, Any]):
    """Load one subscription's metrics only when the selected card consumes them."""

    def __init__(self, loader: Callable[[object], dict[str, Any]], subscription_id: object):
        self._loader = loader
        self._subscription_id = subscription_id
        self._value: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._value is None:
            self._value = dict(self._loader(self._subscription_id) or {})
        return self._value

    def __getitem__(self, key: str) -> Any:
        return self._load()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())


def install_admin_packages_performance(package_ui_module: Any) -> None:
    """Prevent the Packages page from running one metrics RPC per subscription."""

    if getattr(package_ui_module, _PACKAGE_PATCH_MARKER, False):
        return

    import components.package_hardening as package_contract

    def list_member_subscriptions_lazy(member_id: object = "") -> list[dict[str, Any]]:
        query = package_contract._client().table(
            "hm_member_package_subscriptions"
        ).select("*")
        if package_contract._text(member_id):
            query = query.eq("member_id", package_contract._text(member_id))
        rows = package_contract._rows(
            query.order("subscribed_at", desc=True).execute()
        )
        for row in rows:
            row["metrics"] = LazySubscriptionMetrics(
                package_contract.get_subscription_metrics,
                row.get("id"),
            )
            row["inclusions_informational_only"] = True
        return rows

    list_member_subscriptions_lazy._hm_lazy_subscription_metrics = True
    package_ui_module.list_member_subscriptions = list_member_subscriptions_lazy
    setattr(package_ui_module, _PACKAGE_PATCH_MARKER, True)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze(item) for item in value))
    try:
        hash(value)
        return value
    except Exception:
        return repr(value)


def _request_cached(name: str, function: Callable[..., Any]) -> Callable[..., Any]:
    if getattr(function, "_hm_admin_request_cached", False):
        return function

    @functools.wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        cache = _SCHEDULING_REQUEST_CACHE.get()
        if cache is None:
            return function(*args, **kwargs)
        key = (name, _freeze(args), _freeze(kwargs))
        if key not in cache:
            cache[key] = function(*args, **kwargs)
        return copy.deepcopy(cache[key])

    wrapped._hm_admin_request_cached = True
    return wrapped


def _invalidate_request_cache(prefix: str) -> None:
    cache = _SCHEDULING_REQUEST_CACHE.get()
    if cache is None:
        return
    for key in list(cache):
        if str(key[0]).startswith(prefix):
            cache.pop(key, None)


def install_admin_scheduling_performance(scheduling_module: Any) -> None:
    """Reuse pure Scheduling reads within one Streamlit rerun only."""

    if getattr(scheduling_module, _SCHEDULING_PATCH_MARKER, False):
        return

    import components.member_timezone as member_timezone
    import components.schedule_timezone as schedule_timezone

    member_timezone.member_timezone_name = _request_cached(
        "timezone.member",
        member_timezone.member_timezone_name,
    )
    schedule_timezone.member_timezone_name = member_timezone.member_timezone_name
    scheduling_module.member_timezone_name = member_timezone.member_timezone_name

    schedule_timezone.practitioner_timezone_name = _request_cached(
        "timezone.practitioner",
        schedule_timezone.practitioner_timezone_name,
    )
    scheduling_module.practitioner_timezone_name = (
        schedule_timezone.practitioner_timezone_name
    )

    for attribute in (
        "list_members",
        "list_timezone_aware_admin_open_schedules",
        "list_timezone_aware_reschedule_requests",
        "timezone_enriched_schedule_rows",
    ):
        current = getattr(scheduling_module, attribute)
        setattr(
            scheduling_module,
            attribute,
            _request_cached(f"scheduling.{attribute}", current),
        )

    original_persist_timezone = scheduling_module.persist_practitioner_timezone

    @functools.wraps(original_persist_timezone)
    def persist_practitioner_timezone_with_invalidation(*args: Any, **kwargs: Any):
        result = original_persist_timezone(*args, **kwargs)
        _invalidate_request_cache("timezone.practitioner")
        return result

    scheduling_module.persist_practitioner_timezone = (
        persist_practitioner_timezone_with_invalidation
    )
    setattr(scheduling_module, _SCHEDULING_PATCH_MARKER, True)


@contextmanager
def admin_scheduling_render_scope(scheduling_module: Any):
    """Activate request-local Scheduling memoization and always clear it afterward."""

    install_admin_scheduling_performance(scheduling_module)
    token = _SCHEDULING_REQUEST_CACHE.set({})
    try:
        yield
    finally:
        _SCHEDULING_REQUEST_CACHE.reset(token)
