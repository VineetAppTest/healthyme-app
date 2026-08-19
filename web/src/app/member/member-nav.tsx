"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./member-shell.module.css";

const destinations = [
  { href: "/member/today", label: "Today" },
  { href: "/member/plan", label: "Plan" },
  { href: "/member/log", label: "Log" },
  { href: "/member/more", label: "More" },
];

export function MemberNav({ mobile = false }: { mobile?: boolean }) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Member navigation"
      className={mobile ? styles.bottomNav : styles.desktopNav}
    >
      {destinations.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            aria-current={active ? "page" : undefined}
            className={`${styles.navLink} ${active ? styles.navLinkActive : ""}`}
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
