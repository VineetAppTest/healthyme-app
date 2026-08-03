from __future__ import annotations

import sys


_INSTALLED = False
_MARKER = "_hm_profile_builder_canonical_repository_runtime_v1"


def install_profile_builder_canonical_repository_runtime() -> None:
    """Install the Phase 2 canonical source save bridge before Builder imports.

    The live Builder reads canonical repository options directly through
    ``profile_builder_canonical_sources``. This installer keeps module persistence
    aligned with those ID-based rows without changing the public module-store API.
    It is intentionally transitional and can be removed when the canonical store
    becomes the primary implementation in the later cleanup phase.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    import components.profile_builder_module_store as module_store
    import components.profile_builder_module_store_canonical as canonical_store

    module_store._normalise_item_rows = canonical_store._normalise_item_rows
    module_store.save_profile_module = canonical_store.save_profile_module
    setattr(module_store, _MARKER, True)

    # Defensive support for import-order variations in tests or warm Streamlit
    # processes. Normal production installation happens before pbm_modules imports.
    pbm_modules = sys.modules.get("components.pbm_modules")
    if pbm_modules is not None:
        pbm_modules.save_profile_module = canonical_store.save_profile_module
        setattr(pbm_modules, _MARKER, True)

    _INSTALLED = True
