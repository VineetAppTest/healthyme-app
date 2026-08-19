import { redirect } from "next/navigation";

import { isAdminRole, isMemberRole } from "@/features/auth/app-user";
import { getAuthenticatedHealthyMeUser } from "@/features/auth/current-user";

export default async function AdminMigrationHoldingPage() {
  const appUser = await getAuthenticatedHealthyMeUser();
  if (!appUser) redirect("/login");
  if (isMemberRole(appUser.role)) redirect("/member/today");
  if (!isAdminRole(appUser.role)) redirect("/login");

  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">Migration boundary</p>
        <h1>Admin remains on the current HealthyMe web app.</h1>
        <p className="lead">
          The migration is proceeding member-first. This preview confirms the
          canonical Admin role without replacing any Admin workflow yet.
        </p>
      </section>
    </main>
  );
}
