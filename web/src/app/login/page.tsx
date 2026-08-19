import { redirect } from "next/navigation";

import { APP_NAME } from "@/lib/brand";
import {
  isAdminRole,
  isMemberRole,
} from "@/features/auth/app-user";
import { getAuthenticatedHealthyMeUser } from "@/features/auth/current-user";

import { LoginForm } from "./login-form";
import styles from "./login.module.css";

type LoginPageProps = {
  searchParams: Promise<{ logout?: string }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;

  try {
    const appUser = await getAuthenticatedHealthyMeUser();
    if (appUser && isMemberRole(appUser.role)) redirect("/member/today");
    if (appUser && isAdminRole(appUser.role)) redirect("/admin");
  } catch {
    // The page must still render before the HealthyMe preview environment is wired.
  }

  return (
    <main className={styles.page}>
      <section className={styles.shell}>
        <div className={styles.intro}>
          <div>
            <p className={styles.brand}>{APP_NAME}</p>
            <p className={styles.eyebrow}>Member experience</p>
            <h1 className={styles.title}>Your health guidance, when you need it.</h1>
            <p className={styles.copy}>
              The new member web experience is being built around what matters
              now and what you should do next, while keeping your existing
              HealthyMe account and data.
            </p>
          </div>
          <p className={styles.security}>
            Existing HealthyMe Supabase authentication and authorization remain
            authoritative. There is no public sign-up.
          </p>
        </div>

        <div className={styles.panel}>
          <h2>Sign in</h2>
          <p className={styles.panelCopy}>
            Use your existing authorized HealthyMe account.
          </p>
          {params.logout === "1" ? (
            <div className={styles.success}>You have been signed out securely.</div>
          ) : null}
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
