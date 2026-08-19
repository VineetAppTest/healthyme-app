"use server";

import { redirect } from "next/navigation";

import {
  isAdminRole,
  isMemberRole,
  resolveCanonicalAppUser,
} from "@/features/auth/app-user";
import { createClient } from "@/lib/supabase/server";

export type LoginState = {
  error: string;
};

export async function signIn(
  _previousState: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { error: "Enter both email and password." };
  }

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error || !data.user) {
    return { error: "Sign-in failed. Check your email and password." };
  }

  let appUser;
  try {
    appUser = await resolveCanonicalAppUser({
      authUserId: data.user.id,
      email: data.user.email,
    });
  } catch {
    await supabase.auth.signOut();
    return {
      error:
        "HealthyMe authorization is not configured for this preview. No account changes were made.",
    };
  }

  if (!appUser || !appUser.isActive) {
    await supabase.auth.signOut();
    return {
      error:
        "This account is authenticated but is not an active authorized HealthyMe user.",
    };
  }

  if (isMemberRole(appUser.role)) {
    redirect("/member/today");
  }

  if (isAdminRole(appUser.role)) {
    redirect("/admin");
  }

  await supabase.auth.signOut();
  return {
    error: "This HealthyMe role is not enabled in the migration preview yet.",
  };
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/login?logout=1");
}
