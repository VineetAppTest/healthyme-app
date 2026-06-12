
import os
import re
import time
import mimetypes
from pathlib import Path

try:
    from supabase import create_client
except Exception:
    create_client = None


PUBLIC_BUCKET = os.getenv("HEALTHYME_PUBLIC_ASSETS_BUCKET", "healthyme-public-assets")
PRIVATE_BUCKET = os.getenv("HEALTHYME_PRIVATE_ASSETS_BUCKET", "healthyme-private-content-assets")
SIGNED_URL_TTL_SECONDS = int(os.getenv("HEALTHYME_SIGNED_URL_TTL_SECONDS", "21600"))  # 6 hours

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _get_supabase_client():
    if create_client is None:
        raise RuntimeError("Supabase client package is not available.")

    url = (
        os.getenv("SUPABASE_URL")
        or os.getenv("SUPABASE_PROJECT_URL")
        or os.getenv("st_supabase_url")
    )
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("st_supabase_key")
    )
    if not url or not key:
        raise RuntimeError("Supabase URL/key environment variables are not configured.")
    return create_client(url, key)


def safe_slug(value):
    value = (value or "asset").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "asset"


def validate_image_file(uploaded_file):
    if uploaded_file is None:
        return False, "No file uploaded."

    mime = getattr(uploaded_file, "type", "") or mimetypes.guess_type(getattr(uploaded_file, "name", ""))[0] or ""
    if mime not in ALLOWED_IMAGE_TYPES:
        return False, "Only JPG, PNG and WEBP images are allowed."

    size = getattr(uploaded_file, "size", None)
    if size is not None and size > 5 * 1024 * 1024:
        return False, "Image must be 5 MB or smaller."

    return True, ""


def build_asset_path(module, title, uploaded_file):
    mime = getattr(uploaded_file, "type", "") or mimetypes.guess_type(getattr(uploaded_file, "name", ""))[0] or "image/jpeg"
    ext = ALLOWED_IMAGE_TYPES.get(mime)
    if not ext:
        suffix = Path(getattr(uploaded_file, "name", "image.jpg")).suffix.lower()
        ext = suffix if suffix in [".jpg", ".jpeg", ".png", ".webp"] else ".jpg"
    if ext == ".jpeg":
        ext = ".jpg"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{module}/{safe_slug(title)}_{stamp}{ext}"


def upload_content_image(uploaded_file, module, title, access_type="public"):
    ok, message = validate_image_file(uploaded_file)
    if not ok:
        raise ValueError(message)

    access_type = (access_type or "public").strip().lower()
    bucket = PRIVATE_BUCKET if access_type == "private" else PUBLIC_BUCKET
    path = build_asset_path(module, title, uploaded_file)

    content_type = getattr(uploaded_file, "type", None) or "image/jpeg"
    payload = uploaded_file.getvalue()

    client = _get_supabase_client()
    try:
        client.storage.from_(bucket).upload(
            path,
            payload,
            file_options={
                "content-type": content_type,
                "upsert": "true",
            },
        )
    except TypeError:
        # Older supabase-py versions use file_options differently.
        client.storage.from_(bucket).upload(path, payload)

    return {
        "image_bucket": bucket,
        "image_path": path,
        "image_access_type": access_type,
        "image_url": get_asset_display_url(bucket, path, access_type),
    }


def get_asset_display_url(bucket, path, access_type="public"):
    bucket = (bucket or "").strip()
    path = (path or "").strip()
    access_type = (access_type or "public").strip().lower()

    if not bucket or not path:
        return ""

    client = _get_supabase_client()

    if access_type == "private":
        try:
            signed = client.storage.from_(bucket).create_signed_url(path, SIGNED_URL_TTL_SECONDS)
            if isinstance(signed, dict):
                return signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url") or signed.get("url") or ""
            return str(signed or "")
        except Exception:
            return ""

    try:
        public = client.storage.from_(bucket).get_public_url(path)
        if isinstance(public, dict):
            return public.get("publicURL") or public.get("publicUrl") or public.get("public_url") or public.get("url") or ""
        return str(public or "")
    except Exception:
        return ""


def resolve_content_image_url(row, fallback_url=""):
    image_path = str(row.get("image_path", "") or "").strip()
    image_bucket = str(row.get("image_bucket", "") or "").strip()
    image_access_type = str(row.get("image_access_type", "public") or "public").strip().lower()
    manual_url = str(row.get("image_url", "") or "").strip()

    if image_path and image_bucket:
        resolved = get_asset_display_url(image_bucket, image_path, image_access_type)
        if resolved:
            return resolved

    if manual_url.startswith("http://") or manual_url.startswith("https://"):
        return manual_url

    return fallback_url
