import styles from "./today.module.css";

const buckets = [
  {
    title: "Now",
    badge: "Current",
    empty:
      "Current member context will appear here after the existing HealthyMe plan/task read contracts are connected and validated.",
    primary: true,
  },
  {
    title: "Next",
    badge: "Up next",
    empty: "The next meaningful member action will be derived from existing HealthyMe state.",
  },
  {
    title: "Later",
    badge: "Upcoming",
    empty: "Later items will stay compact until they become relevant.",
  },
  {
    title: "Done",
    badge: "Confirmed",
    empty:
      "Only authoritative HealthyMe completion or acknowledgement states will appear here.",
  },
];

export default function TodayPage() {
  return (
    <>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Member journey</p>
          <h1 className={styles.title}>Today</h1>
          <p className={styles.sub}>What matters now, and what comes next.</p>
        </div>
      </header>

      <div className={styles.gate}>
        <strong>Migration preview:</strong> the member shell is live on the migration
        branch, but real health/plan data is intentionally not rendered until the
        existing HealthyMe read contracts are wired and validated. No backend data
        or logic has been changed.
      </div>

      <div className={styles.grid}>
        <div className={styles.stack}>
          {buckets
            .filter((bucket) => bucket.primary)
            .map((bucket) => (
              <section
                className={`${styles.section} ${styles.sectionPrimary}`}
                key={bucket.title}
              >
                <div className={styles.sectionHead}>
                  <h2 className={styles.sectionTitle}>{bucket.title}</h2>
                  <span className={styles.badge}>{bucket.badge}</span>
                </div>
                <div className={styles.empty}>{bucket.empty}</div>
              </section>
            ))}
          {buckets
            .filter((bucket) => bucket.title === "Next")
            .map((bucket) => (
              <section className={styles.section} key={bucket.title}>
                <div className={styles.sectionHead}>
                  <h2 className={styles.sectionTitle}>{bucket.title}</h2>
                  <span className={styles.badge}>{bucket.badge}</span>
                </div>
                <div className={styles.empty}>{bucket.empty}</div>
              </section>
            ))}
        </div>

        <div className={styles.stack}>
          {buckets
            .filter((bucket) => ["Later", "Done"].includes(bucket.title))
            .map((bucket) => (
              <section className={styles.section} key={bucket.title}>
                <div className={styles.sectionHead}>
                  <h2 className={styles.sectionTitle}>{bucket.title}</h2>
                  <span className={styles.badge}>{bucket.badge}</span>
                </div>
                <div className={styles.empty}>{bucket.empty}</div>
              </section>
            ))}
        </div>
      </div>
    </>
  );
}
