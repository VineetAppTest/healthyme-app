import "server-only";

import { createAdminClient } from "@/lib/supabase/admin";

export type HealthyMeAppUser = {
  id: string;
  name: string;
  email: string;
  role: string;
  isActive: boolean;
  authProvider: string;
  mustResetPassword: boolean;
  authUserId: string;
};

type HmUserRow = {
  id?: unknown;
  name?: unknown;
  email?: unknown;
  role?: unknown;
  is_active?: unknown;
  auth_provider?: unknown;
  must_reset_password?: unknown;
  auth_user_id?: unknown;
};

function clean(value: unknown) {
  return String(value ?? "").trim();
}

function normalizeEmail(value: unknown) {
  return clean(value).toLowerCase();
}

function normalizeRole(value: unknown) {
  return clean(value || "member").toLowerCase().replaceAll(" ", "_");
}

function toAppUser(row: HmUserRow | null | undefined): HealthyMeAppUser | null {
  if (!row || row.is_active === false) return null;

  const email = normalizeEmail(row.email);
  return {
    id: clean(row.id),
    name: clean(row.name || row.email || "User"),
    email,
    role: normalizeRole(row.role),
    isActive: row.is_active !== false,
    authProvider: clean(row.auth_provider || "supabase"),
    mustResetPassword: Boolean(row.must_reset_password),
    authUserId: clean(row.auth_user_id),
  };
}

const SELECT_COLUMNS =
  "id,name,email,role,is_active,auth_provider,must_reset_password,auth_user_id";

/**
 * Reproduce HealthyMe's canonical role lookup without changing the backend.
 * Lookup order intentionally matches the current Streamlit role model:
 * auth.users.id -> hm_users.auth_user_id, then unique lower/email fallback.
 */
export async function resolveCanonicalAppUser(params: {
  email?: string | null;
  authUserId?: string | null;
}): Promise<HealthyMeAppUser | null> {
  const authUserId = clean(params.authUserId);
  const email = normalizeEmail(params.email);
  const supabase = createAdminClient();

  if (authUserId) {
    const { data, error } = await supabase
      .from("hm_users")
      .select(SELECT_COLUMNS)
      .eq("auth_user_id", authUserId)
      .limit(1);

    if (!error && data?.length) {
      return toAppUser(data[0] as HmUserRow);
    }
  }

  if (!email) return null;

  const { data, error } = await supabase
    .from("hm_users")
    .select(SELECT_COLUMNS)
    .ilike("email", email)
    .limit(2);

  if (error || data?.length !== 1) return null;
  return toAppUser(data[0] as HmUserRow);
}

export function isMemberRole(role: unknown) {
  return normalizeRole(role) === "member";
}

export function isAdminRole(role: unknown) {
  return ["admin", "super_admin"].includes(normalizeRole(role));
}
