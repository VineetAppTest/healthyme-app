def normalize_admin_score(value, default="NA"):
    """Normalize stored member/admin values for admin linked fields.

    Handles both strings and numbers so values like 1 / 1.0 / "1" all populate.
    """
    if value is None:
        return default
    raw = str(value).strip()
    if raw in ["", "Select", "None", "nan"]:
        return default
    upper = raw.upper()
    if upper in ["NA", "N/A", "NOT APPLICABLE"]:
        return "NA"
    if raw in ["1", "2", "3"]:
        return raw
    if raw in ["1.0", "2.0", "3.0"]:
        return raw[0]
    return default

def resolve_admin_linked_value(item, nsp1=None, nsp2=None, laf=None, stored="Select"):
    """Resolve one admin assessment item from NSP/LAF/manual stores.

    Priority:
    1. Explicit linked_code from NSP1/NSP2/LAF.
    2. Stored admin value if source value is unavailable.
    3. NA fallback for linked items.

    This function does not touch Auth0, Supabase connection, or login.
    """
    nsp1 = nsp1 or {}
    nsp2 = nsp2 or {}
    laf = laf or {}

    linked_code = item.get("linked_code")
    if not linked_code:
        return normalize_admin_score(stored, default=stored if stored in ["Select", "NA", "1", "2", "3"] else "Select"), {
            "source_type": "Manual",
            "source_code": "",
            "source_value": stored,
            "source_label": "Manual admin input",
        }

    code = str(linked_code).strip()
    raw = None
    source_type = "Linked"

    if code.startswith("nsp1_"):
        raw = nsp1.get(code)
        source_type = "NSP Page 1"
    elif code.startswith("nsp2_"):
        raw = nsp2.get(code)
        source_type = "NSP Page 2"
    else:
        # Future-proofing for approved LAF-linked admin items.
        raw = laf.get(code)
        source_type = "LAF"

    val = normalize_admin_score(raw, default=None)

    if val is None:
        # Use prior admin stored value if a linked source is temporarily blank.
        val = normalize_admin_score(stored, default="NA")

    return val, {
        "source_type": source_type,
        "source_code": code,
        "source_value": raw,
        "source_label": f"{source_type}: {code}",
    }