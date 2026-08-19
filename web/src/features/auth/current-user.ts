import "server-only";

import { createClient } from "@/lib/supabase/server";
import {
  resolveCanonicalAppUser,
  type HealthyMeAppUser,
} from "@/features/auth/app-user";

export type AuthenticatedHealthyMeUser = HealthyMeAppUser & {
  authUserId: string;
};

export async function getAuthenticatedHealthyMeUser(): Promise<AuthenticatedHealthyMeUser | null> {
  const supabase = await createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) return null;

  const appUser = await resolveCanonicalAppUser({
    authUserId: user.id,
    email: user.email,
  });

  if (!appUser) return null;

  return {
    ...appUser,
    authUserId: user.id,
  };
}
