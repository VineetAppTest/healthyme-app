"use client";

import { useActionState } from "react";

import { signIn, type LoginState } from "./actions";
import styles from "./login.module.css";

const initialState: LoginState = { error: "" };

export function LoginForm() {
  const [state, formAction, pending] = useActionState(signIn, initialState);

  return (
    <form action={formAction} className={styles.form}>
      <label className={styles.field}>
        <span>Email</span>
        <input
          autoComplete="email"
          inputMode="email"
          name="email"
          required
          type="email"
        />
      </label>

      <label className={styles.field}>
        <span>Password</span>
        <input
          autoComplete="current-password"
          name="password"
          required
          type="password"
        />
      </label>

      {state.error ? (
        <div aria-live="polite" className={styles.error} role="alert">
          {state.error}
        </div>
      ) : null}

      <button className={styles.submit} disabled={pending} type="submit">
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
