import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.111.0";

const APP_STATE_ID = "healthyme_app_state_v1";
const EVENT_TABLE = "hm_consultation_reminder_events";
const RESEND_ENDPOINT = "https://api.resend.com/emails";
const DEFAULT_TIMEZONE = "Asia/Kolkata";
const MAX_EMAIL_ATTEMPTS = 4;
const STALE_SENDING_MINUTES = 15;

type UnknownRecord = Record<string, unknown>;
type ReminderStage = "72h_action" | "24h_action" | "24h_info";

type ReminderEvent = {
  id: string;
  schedule_id: string;
  member_id: string;
  member_email: string;
  stage: ReminderStage;
  scheduled_start_at_utc: string;
  subject: string;
  message: string;
  details: UnknownRecord;
  email_to: string;
  email_status: string;
  email_attempt_count: number;
};

function text(value: unknown): string {
  return String(value ?? "").trim();
}

function record(value: unknown): UnknownRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as UnknownRecord
    : {};
}

function records(value: unknown): UnknownRecord[] {
  return Array.isArray(value)
    ? value.filter((row) => row && typeof row === "object") as UnknownRecord[]
    : [];
}

function envSecretKey(): string {
  const modern = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (modern) {
    try {
      const parsed = JSON.parse(modern) as Record<string, string>;
      if (text(parsed.default)) return text(parsed.default);
      const first = Object.values(parsed).find((value) => text(value));
      if (first) return text(first);
    } catch {
      // Fall through to the legacy key for backwards compatibility.
    }
  }
  return text(Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"));
}

function parseClock(value: unknown): { hour: number; minute: number } | null {
  const raw = text(value).toUpperCase();
  if (!raw) return null;

  const twelveHour = raw.match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$/);
  if (twelveHour) {
    let hour = Number.parseInt(twelveHour[1], 10);
    const minute = Number.parseInt(twelveHour[2] ?? "0", 10);
    if (hour < 1 || hour > 12 || minute < 0 || minute > 59) return null;
    if (hour === 12) hour = 0;
    if (twelveHour[3] === "PM") hour += 12;
    return { hour, minute };
  }

  const twentyFourHour = raw.match(/^(\d{1,2})(?::(\d{2}))?$/);
  if (!twentyFourHour) return null;
  const hour = Number.parseInt(twentyFourHour[1], 10);
  const minute = Number.parseInt(twentyFourHour[2] ?? "0", 10);
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
  return { hour, minute };
}

function localPartsAt(date: Date, timezone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return {
    year: Number.parseInt(values.year ?? "0", 10),
    month: Number.parseInt(values.month ?? "0", 10),
    day: Number.parseInt(values.day ?? "0", 10),
    hour: Number.parseInt(values.hour ?? "0", 10),
    minute: Number.parseInt(values.minute ?? "0", 10),
  };
}

function legacyScheduleStartUtc(schedule: UnknownRecord): Date | null {
  const dateMatch = text(schedule.schedule_date).match(/^(\d{4})-(\d{2})-(\d{2})/);
  const clock = parseClock(schedule.start_time);
  if (!dateMatch || !clock) return null;

  const timezone = text(schedule.member_timezone_name) || DEFAULT_TIMEZONE;
  const desired = {
    year: Number.parseInt(dateMatch[1], 10),
    month: Number.parseInt(dateMatch[2], 10),
    day: Number.parseInt(dateMatch[3], 10),
    hour: clock.hour,
    minute: clock.minute,
  };
  const desiredPseudoUtc = Date.UTC(
    desired.year,
    desired.month - 1,
    desired.day,
    desired.hour,
    desired.minute,
  );

  let candidateMs = desiredPseudoUtc;
  try {
    // Iteratively translate the wall-clock time in an IANA timezone to UTC.
    // Current HealthyMe schedules normally carry start_at_utc; this is only a
    // compatibility path for older rows.
    for (let index = 0; index < 3; index += 1) {
      const observed = localPartsAt(new Date(candidateMs), timezone);
      const observedPseudoUtc = Date.UTC(
        observed.year,
        observed.month - 1,
        observed.day,
        observed.hour,
        observed.minute,
      );
      candidateMs += desiredPseudoUtc - observedPseudoUtc;
    }
    const check = localPartsAt(new Date(candidateMs), timezone);
    if (
      check.year !== desired.year
      || check.month !== desired.month
      || check.day !== desired.day
      || check.hour !== desired.hour
      || check.minute !== desired.minute
    ) {
      return null;
    }
    return new Date(candidateMs);
  } catch {
    return null;
  }
}

function scheduleStartUtc(schedule: UnknownRecord): Date | null {
  const canonical = text(schedule.start_at_utc);
  if (canonical) {
    const parsed = new Date(canonical);
    if (!Number.isNaN(parsed.getTime())) return parsed;
  }
  return legacyScheduleStartUtc(schedule);
}

function scheduleStatus(schedule: UnknownRecord): string {
  return text(schedule.status || "scheduled").toLowerCase();
}

function hasPendingReschedule(schedule: UnknownRecord): boolean {
  return text(schedule.reschedule_request_status).toLowerCase() === "pending";
}

function stageForSchedule(schedule: UnknownRecord, now: Date): ReminderStage | null {
  const status = scheduleStatus(schedule);
  if (["cancelled", "completed", "rescheduled"].includes(status)) return null;
  if (hasPendingReschedule(schedule)) return null;

  const start = scheduleStartUtc(schedule);
  if (!start) return null;
  const hours = (start.getTime() - now.getTime()) / 3_600_000;
  if (hours <= 0 || hours > 72) return null;

  if (hours <= 24) {
    if (status === "scheduled") return "24h_action";
    if (status === "acknowledged") return "24h_info";
    return null;
  }

  return status === "scheduled" ? "72h_action" : null;
}

function stageStillValid(stage: ReminderStage, schedule: UnknownRecord, now: Date): boolean {
  const current = stageForSchedule(schedule, now);
  if (stage === "72h_action") return current === "72h_action";
  if (stage === "24h_action") return current === "24h_action";
  return current === "24h_info";
}

function memberEmail(state: UnknownRecord, schedule: UnknownRecord): string {
  const direct = text(schedule.member_email);
  if (direct) return direct;
  const memberId = text(schedule.member_id).toLowerCase();
  const user = records(state.users).find((row) => {
    const id = text(row.id).toLowerCase();
    const email = text(row.email).toLowerCase();
    return memberId && (id === memberId || email === memberId);
  });
  return text(user?.email);
}

function memberName(state: UnknownRecord, schedule: UnknownRecord): string {
  if (text(schedule.member_name)) return text(schedule.member_name);
  const memberId = text(schedule.member_id).toLowerCase();
  const user = records(state.users).find((row) => {
    const id = text(row.id).toLowerCase();
    const email = text(row.email).toLowerCase();
    return memberId && (id === memberId || email === memberId);
  });
  return text(user?.name || user?.full_name);
}

function consultationWhen(schedule: UnknownRecord): { date: string; time: string; timezone: string } {
  const start = scheduleStartUtc(schedule);
  const timezone = text(schedule.member_timezone_name) || DEFAULT_TIMEZONE;
  if (!start) {
    return {
      date: text(schedule.schedule_date),
      time: [text(schedule.start_time), text(schedule.end_time)].filter(Boolean).join(" – "),
      timezone,
    };
  }
  try {
    const date = new Intl.DateTimeFormat("en-GB", {
      timeZone: timezone,
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(start);
    const time = new Intl.DateTimeFormat("en-GB", {
      timeZone: timezone,
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    }).format(start);
    return { date, time, timezone };
  } catch {
    return {
      date: text(schedule.schedule_date),
      time: text(schedule.start_time),
      timezone,
    };
  }
}

function reminderCopy(stage: ReminderStage, schedule: UnknownRecord) {
  const title = text(schedule.title || schedule.schedule_type) || "HealthyMe consultation";
  const when = consultationWhen(schedule);
  const timing = `${when.date} at ${when.time}${when.timezone ? ` (${when.timezone})` : ""}`;

  if (stage === "72h_action") {
    return {
      subject: "Action required: Please confirm your HealthyMe consultation",
      message: `${title} is scheduled for ${timing}. Please Accept or Reschedule. If you need a different time, send the reschedule request before the final 24-hour window. Requests raised within 24 hours may not be accepted and, if accommodated, may use an additional session.`,
    };
  }
  if (stage === "24h_action") {
    return {
      subject: "Final reminder: Your HealthyMe consultation is within 24 hours",
      message: `${title} is scheduled for ${timing} and is still awaiting acceptance. Please Accept now. If you need to reschedule, submit the request immediately. Requests raised within 24 hours may not be accepted and, if accommodated, may use an additional session.`,
    };
  }
  return {
    subject: "Reminder: Your HealthyMe consultation is coming up",
    message: `Your accepted consultation, ${title}, is scheduled for ${timing}. Please keep the scheduled time available and use the HealthyMe consultation details to join the session.`,
  };
}

function htmlEscape(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function emailHtml(name: string, subject: string, message: string, appUrl: string): string {
  return `<!doctype html>
<html><body style="margin:0;background:#F7F4EC;font-family:Arial,Helvetica,sans-serif;color:#334155">
<div style="max-width:640px;margin:0 auto;padding:24px 14px">
<div style="background:linear-gradient(135deg,#064E3B,#0F766E);border-radius:18px 18px 0 0;padding:22px 24px;color:#fff">
<div style="font-size:22px;font-weight:800">HealthyMe</div><div style="font-size:13px;opacity:.9;margin-top:4px">Consultation reminder</div></div>
<div style="background:#fff;border:1px solid #E3C98E;border-top:0;border-radius:0 0 18px 18px;padding:24px">
<p>Dear ${htmlEscape(name || "there")},</p><h1 style="font-size:20px;line-height:1.35;color:#064E3B">${htmlEscape(subject)}</h1>
<p style="font-size:15px;line-height:1.65">${htmlEscape(message)}</p>
<div style="margin:22px 0 8px"><a href="${htmlEscape(appUrl)}" style="display:inline-block;background:#064E3B;color:#fff;text-decoration:none;padding:11px 18px;border-radius:10px;font-weight:700">Open HealthyMe</a></div>
<p style="font-size:13px;color:#64748B">Warm regards,<br><strong style="color:#064E3B">Team HealthyMe</strong></p>
</div></div></body></html>`;
}

async function sendResend(event: ReminderEvent, name: string) {
  const apiKey = text(Deno.env.get("RESEND_API_KEY"));
  const sender = text(
    Deno.env.get("RESEND_FROM_EMAIL")
      || Deno.env.get("RESEND_FROM")
      || Deno.env.get("EMAIL_FROM"),
  );
  const replyTo = text(Deno.env.get("RESEND_REPLY_TO") || Deno.env.get("EMAIL_REPLY_TO"));
  const appUrl = text(Deno.env.get("HEALTHYME_APP_URL")) || "https://healthyme.in";

  if (!apiKey || !sender) {
    return { status: "configuration_missing", providerId: "", error: "RESEND_API_KEY and RESEND_FROM_EMAIL/RESEND_FROM are required." };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(event.email_to)) {
    return { status: "failed", providerId: "", error: "A valid member email address is not available." };
  }

  const payload: UnknownRecord = {
    from: sender.includes("<") ? sender : `HealthyMe <${sender}>`,
    to: [event.email_to],
    subject: event.subject,
    html: emailHtml(name, event.subject, event.message, appUrl),
    text: `Dear ${name || "there"},\n\n${event.subject}\n\n${event.message}\n\nOpen HealthyMe: ${appUrl}\n\nWarm regards,\nTeam HealthyMe`,
  };
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(replyTo)) payload.reply_to = replyTo;

  try {
    const response = await fetch(RESEND_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "Idempotency-Key": `healthyme-consultation|${event.schedule_id}|${event.stage}`,
      },
      body: JSON.stringify(payload),
    });
    let body: UnknownRecord = {};
    try {
      body = record(await response.json());
    } catch {
      body = {};
    }
    if (response.ok) {
      return { status: "sent", providerId: text(body.id), error: "" };
    }
    return {
      status: "failed",
      providerId: "",
      error: text(body.message || record(body.error).message) || `Resend returned HTTP ${response.status}.`,
    };
  } catch (error) {
    return { status: "failed", providerId: "", error: text(error) || "Resend request failed." };
  }
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return Response.json({ error: "Method not allowed" }, { status: 405 });

  const supabaseUrl = text(Deno.env.get("SUPABASE_URL"));
  const secretKey = envSecretKey();
  if (!supabaseUrl || !secretKey) {
    console.error("consultation-reminders: Supabase admin environment is unavailable");
    return Response.json({ error: "Server configuration unavailable" }, { status: 500 });
  }

  const admin = createClient(supabaseUrl, secretKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const presentedCronSecret = text(req.headers.get("x-healthyme-cron-secret"));
  const { data: authorized, error: authError } = await admin.rpc(
    "hm_verify_consultation_cron_secret",
    { p_secret: presentedCronSecret },
  );
  if (authError || authorized !== true) {
    console.warn("consultation-reminders: rejected unauthorised invocation");
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const now = new Date();
  const { data: stateRow, error: stateError } = await admin
    .from("healthyme_app_state")
    .select("data")
    .eq("id", APP_STATE_ID)
    .maybeSingle();
  if (stateError) {
    console.error("consultation-reminders: app-state read failed", stateError.message);
    return Response.json({ error: "HealthyMe state could not be read" }, { status: 500 });
  }

  const state = record(stateRow?.data);
  const schedules = records(state.schedules);
  const scheduleById = new Map<string, UnknownRecord>();
  let eligible = 0;
  let created = 0;

  for (const schedule of schedules) {
    const scheduleId = text(schedule.id);
    if (!scheduleId) continue;
    scheduleById.set(scheduleId, schedule);
    const stage = stageForSchedule(schedule, now);
    if (!stage) continue;
    const start = scheduleStartUtc(schedule);
    if (!start) continue;
    eligible += 1;

    const copy = reminderCopy(stage, schedule);
    const email = memberEmail(state, schedule);
    const event = {
      schedule_id: scheduleId,
      member_id: text(schedule.member_id),
      member_email: email,
      stage,
      scheduled_start_at_utc: start.toISOString(),
      subject: copy.subject,
      message: copy.message,
      details: {
        title: text(schedule.title || schedule.schedule_type),
        schedule_date: text(schedule.schedule_date),
        start_time: text(schedule.start_time),
        end_time: text(schedule.end_time),
        timezone: text(schedule.member_timezone_name) || DEFAULT_TIMEZONE,
        mode: text(schedule.mode),
        location_or_link: text(schedule.location_or_link),
      },
      email_to: email,
      email_status: "pending",
      updated_at: now.toISOString(),
    };

    const { data: inserted, error: insertError } = await admin
      .from(EVENT_TABLE)
      .upsert(event, { onConflict: "schedule_id,stage", ignoreDuplicates: true })
      .select("id")
      .maybeSingle();
    if (insertError) {
      console.error("consultation-reminders: event insert failed", scheduleId, stage, insertError.message);
      continue;
    }
    if (inserted?.id) created += 1;
  }

  const resendConfigured = Boolean(
    text(Deno.env.get("RESEND_API_KEY"))
    && text(Deno.env.get("RESEND_FROM_EMAIL") || Deno.env.get("RESEND_FROM") || Deno.env.get("EMAIL_FROM")),
  );

  if (!resendConfigured) {
    const { error: configMarkError } = await admin
      .from(EVENT_TABLE)
      .update({ email_status: "configuration_missing", updated_at: now.toISOString() })
      .eq("email_status", "pending");
    if (configMarkError) console.warn("consultation-reminders: could not mark missing email configuration", configMarkError.message);
    console.warn("consultation-reminders: Resend configuration is missing; reminders were staged but email was not attempted");
    return Response.json({ ok: true, eligible, created, emailed: 0, emailConfigured: false });
  }

  const staleBefore = new Date(now.getTime() - STALE_SENDING_MINUTES * 60_000).toISOString();
  await admin
    .from(EVENT_TABLE)
    .update({ email_status: "failed", email_error: "Recovered stale delivery claim.", updated_at: now.toISOString() })
    .eq("email_status", "sending")
    .lt("email_attempted_at", staleBefore)
    .lt("email_attempt_count", MAX_EMAIL_ATTEMPTS);

  const { data: pendingRows, error: pendingError } = await admin
    .from(EVENT_TABLE)
    .select("*")
    .in("email_status", ["pending", "failed", "configuration_missing"])
    .lt("email_attempt_count", MAX_EMAIL_ATTEMPTS)
    .order("created_at", { ascending: true })
    .limit(40);
  if (pendingError) {
    console.error("consultation-reminders: pending delivery read failed", pendingError.message);
    return Response.json({ error: "Reminder delivery queue could not be read" }, { status: 500 });
  }

  let emailed = 0;
  let suppressed = 0;
  let failed = 0;

  for (const raw of pendingRows ?? []) {
    const event = raw as ReminderEvent;
    const currentSchedule = scheduleById.get(text(event.schedule_id));
    if (!currentSchedule || !stageStillValid(event.stage, currentSchedule, new Date())) {
      await admin
        .from(EVENT_TABLE)
        .update({ email_status: "suppressed", email_error: "Schedule is no longer eligible for this reminder stage.", updated_at: new Date().toISOString() })
        .eq("id", event.id)
        .eq("email_status", event.email_status);
      suppressed += 1;
      continue;
    }

    const attemptCount = Number(event.email_attempt_count ?? 0) + 1;
    const attemptedAt = new Date().toISOString();
    const { data: claimed, error: claimError } = await admin
      .from(EVENT_TABLE)
      .update({
        email_status: "sending",
        email_attempt_count: attemptCount,
        email_attempted_at: attemptedAt,
        email_error: "",
        updated_at: attemptedAt,
      })
      .eq("id", event.id)
      .eq("email_status", event.email_status)
      .select("*")
      .maybeSingle();
    if (claimError || !claimed) continue;

    const deliveryEvent = claimed as ReminderEvent;
    const delivery = await sendResend(deliveryEvent, memberName(state, currentSchedule));
    const completedAt = new Date().toISOString();
    const sent = delivery.status === "sent";
    const { error: updateError } = await admin
      .from(EVENT_TABLE)
      .update({
        email_status: delivery.status,
        email_provider: "Resend",
        email_provider_id: delivery.providerId,
        email_error: delivery.error.slice(0, 500),
        email_sent_at: sent ? completedAt : null,
        updated_at: completedAt,
      })
      .eq("id", event.id)
      .eq("email_status", "sending");
    if (updateError) {
      console.error("consultation-reminders: delivery audit update failed", event.id, updateError.message);
    }
    if (sent) emailed += 1;
    else failed += 1;
  }

  console.log(JSON.stringify({
    event: "consultation_reminder_run",
    eligible,
    created,
    emailed,
    suppressed,
    failed,
    at: now.toISOString(),
  }));

  return Response.json({ ok: true, eligible, created, emailed, suppressed, failed, emailConfigured: true });
});
