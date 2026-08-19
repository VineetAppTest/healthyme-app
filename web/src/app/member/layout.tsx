import { redirect } from "next/navigation";

import { signOut } from "@/app/login/actions";
import { isAdminRole, isMemberRole } from "@/features/auth/app-user";
import { getAuthenticatedHealthyMeUser } from "@/features/auth/current-user";
import { APP_NAME } from "@/lib/brand";

import { MemberNav } from "./member-nav";
import styles from "./member-shell.module.css";

export default async function MemberLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  let appUser;
  try {
    appUser = await getAuthenticatedHealthyMeUser();
  } catch {
    redirect("/login");
  }

  if (!appUser) redirect("/login");
  if (isAdminRole(appUser.role)) redirect("/admin");
  if (!isMemberRole(appUser.role)) redirect("/login");

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.identity}>
            <p className={styles.brand}>{APP_NAME}</p>
            <p className={styles.memberName}>{appUser.name}</p>
          </div>
          <form action={signOut}>
            <button className={styles.signOut} type="submit">
              Sign out
            </button>
          </form>
        </div>
        <MemberNav />
      </header>

      <main className={styles.main}>{children}</main>
      <MemberNav mobile />
    </div>
  );
}
