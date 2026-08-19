import { APP_NAME } from "@/lib/brand";

const migrationRules = [
  {
    title: "Keep Supabase",
    copy: "Existing database, Auth, RLS, storage, IDs and history remain authoritative.",
  },
  {
    title: "Replace presentation progressively",
    copy: "Each Streamlit workflow is reproduced in Next.js and accepted through UAT before retirement.",
  },
  {
    title: "Protect accepted behaviour",
    copy: "Navigation, role routing, lifecycle rules and member/admin outcomes are migration contracts, not redesign targets.",
  },
];

export default function Home() {
  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">{APP_NAME}</div>
        <div className="status-pill">Next.js migration foundation</div>
      </header>

      <section className="hero">
        <article className="card">
          <p className="eyebrow">Frontend replacement</p>
          <h1>A new interface over the same HealthyMe product.</h1>
          <p className="lead">
            This Next.js application is being introduced alongside the current
            Streamlit implementation. Backend behaviour is preserved while
            screens are migrated and validated one workflow at a time.
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
