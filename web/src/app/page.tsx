import Link from "next/link";

import { APP_NAME } from "@/lib/brand";

const migrationRules = [
  {
    title: "Keep Supabase",
    copy: "Existing database, Auth, RLS, storage, IDs and history remain authoritative.",
  },
  {
    title: "Redesign the experience",
    copy: "Streamlit remains the functional reference, but the new web app is not a page-for-page UX copy.",
  },
  {
    title: "Member first",
    copy: "The first product journey is proactive Today guidance: Now, Next, Later and authoritative Done states.",
  },
];

export default function Home() {
  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">{APP_NAME}</div>
        <div className="status-pill">Next.js migration preview</div>
      </header>

      <section className="hero">
        <article className="card">
          <p className="eyebrow">Member-first frontend replacement</p>
          <h1>A clearer HealthyMe experience over the same product.</h1>
          <p className="lead">
            The new web experience is being introduced alongside Streamlit. It
            keeps the existing HealthyMe backend and business behaviour while
            making the member journey more proactive, intuitive and responsive.
          </p>
          <p>
            <Link href="/login">Open member migration preview →</Link>
          </p>
        </article>

        <aside className="card" aria-label="Migration guardrails">
          <h2>Migration guardrails</h2>
          <ol className="migration-list">
            {migrationRules.map((rule, index) => (
              <li className="migration-item" key={rule.title}>
                <span className="marker">{index + 1}</span>
                <span>
                  <span className="item-title">{rule.title}</span>
                  <span className="item-copy">{rule.copy}</span>
                </span>
              </li>
            ))}
          </ol>
        </aside>
      </section>
    </main>
  );
}
