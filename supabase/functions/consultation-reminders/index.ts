import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.111.0";

const APP_STATE_ID = "healthyme_app_state_v1";
const EVENT_TABLE = "hm_consultation_reminder_events";
const DEFAULT_TIMEZONE = "Asia/Kolkata";
const MAX_EMAIL_ATTEMPTS = 4;
const SMTP_HOST = "smtp.gmail.com";
const SMTP_PORT = 465;
const SMTP_TIMEOUT_MS = 12_000;
const EMAIL_PROVIDER = "Gmail SMTP";

type UnknownRecord = Record<string, unknown>;
type ReminderStage = "72h_action" | "24h_action" | "24h_info";
type DeliveryStatus = "sent" | "failed" | "configuration_missing" | "uncertain";

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

type DeliveryResult = {
  status: DeliveryStatus;
  providerId: string;
  error: string;
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

function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function encodeUtf8Base64(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function foldBase64(value: string): string {
  const raw = encodeUtf8Base64(value);
  const lines: string[] = [];
  for (let index = 0; index < raw.length; index += 76) {
    lines.push(raw.slice(index, index + 76));
  }
  return lines.join("\r\n");
}

function smtpMessage(event: ReminderEvent, name: string, sender: string, appUrl: string): { data: string; messageId: string } {
  const boundary = `healthyme_${event.schedule_id}_${event.stage}`.replace(/[^A-Za-z0-9_-]/g, "_");
  const safeId = event.schedule_id.replace(/[^A-Za-z0-9._-]/g, "_");
  const messageId = `<healthyme-consultation-${safeId}-${event.stage}@gmail.local>`;
  const plain = `Dear ${name || "there"},\n\n${event.subject}\n\n${event.message}\n\nOpen HealthyMe: ${appUrl}\n\nWarm regards,\nTeam HealthyMe`;
  const html = emailHtml(name, event.subject, event.message, appUrl);
  const headers = [
    `From: HealthyMe <${sender}>`,
    `To: <${event.email_to}>`,
    `Subject: ${event.subject}`,
    `Date: ${new Date().toUTCString()}`,
    `Message-ID: ${messageId}`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/alternative; boundary=\"${boundary}\"`,
    "",
  ];
  const body = [
    `--${boundary}`,
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    foldBase64(plain),
    `--${boundary}`,
    "Content-Type: text/html; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    foldBase64(html),
    `--${boundary}--`,
    "",
  ];
  return { data: [...headers, ...body].join("\r\n"), messageId };
}

async function withTimeout<T>(promise: Promise<T>, label: string): Promise<T> {
  let timer: number | undefined;
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => reject(new Error(`${label} timed out`)), SMTP_TIMEOUT_MS);
      }),
    ]);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

async function readSmtpResponse(conn: Deno.Conn): Promise<{ code: number; text: string }> {
  const decoder = new TextDecoder();
  let accumulated = "";
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const buffer = new Uint8Array(4096);
    const count = await withTimeout(conn.read(buffer), "SMTP read");
    if (count === null) throw new Error("SMTP connection closed unexpectedly");
    accumulated += decoder.decode(buffer.subarray(0, count), { stream: true });
    const lines = accumulated.split("\r\n");
    for (const line of lines) {
      const match = line.match(/^(\d{3}) (.*)$/s);
      if (match) {
        return { code: Number.parseInt(match[1], 10), text: accumulated.trim() };
      }
    }
  }
  throw new Error("SMTP response was incomplete");
}

async function smtpCommand(conn: Deno.Conn, command: string, expected: number[]): Promise<{ code: number; text: string }> {
  const encoded = new TextEncoder().encode(`${command}\r\n`);
  await withTimeout(conn.write(encoded), "SMTP write");
  const response = await readSmtpResponse(conn);
  if (!expected.includes(response.code)) {
    throw new Error(`SMTP ${response.code}: ${response.text.slice(0, 240)}`);
  }
  return response;
}

async function sendGmailSmtp(event: ReminderEvent, name: string): Promise<DeliveryResult> {
  const sender = text(Deno.env.get("HEALTHYME_GMAIL_USER"));
  const appPassword = text(Deno.env.get("HEALTHYME_GMAIL_APP_PASSWORD")).replace(/\s+/g, "");
  const appUrl = text(Deno.env.get("HEALTHYME_APP_URL")) || "https://healthyme.in";

  if (!isEmail(sender) || !appPassword) {
    return {
      status: "configuration_missing",
      providerId: "",
      error: "HEALTHYME_GMAIL_USER and HEALTHYME_GMAIL_APP_PASSWORD are required.",
    };
  }
  if (!isEmail(event.email_to)) {
    return { status: "failed", providerId: "", error: "A valid member email address is not available." };
  }

  let conn: Deno.Conn | null = null;
  let dataAccepted = false;
  let dataStarted = false;
  const message = smtpMessage(event, name, sender, appUrl);

  try {
    conn = await withTimeout(Deno.connectTls({ hostname: SMTP_HOST, port: SMTP_PORT }), "SMTP connect");
    const greeting = await readSmtpResponse(conn);
    if (greeting.code !== 220) throw new Error(`SMTP ${greeting.code}: ${greeting.text.slice(0, 240)}`);

    await smtpCommand(conn, "EHLO healthyme.in", [250]);
    await smtpCommand(conn, "AUTH LOGIN", [334]);
    await smtpCommand(conn, btoa(sender), [334]);
    await smtpCommand(conn, btoa(appPassword), [235]);
    await smtpCommand(conn, `MAIL FROM:<${sender}>`, [250]);
    await smtpCommand(conn, `RCPT TO:<${event.email_to}>`, [250, 251]);
    await smtpCommand(conn, "DATA", [354]);
    dataStarted = true;

    const dotStuffed = message.data
      .split("\r\n")
      .map((line) => line.startsWith(".") ? `.${line}` : line)
      .join("\r\n");
    await withTimeout(conn.write(new TextEncoder().encode(`${dotStuffed}\r\n.\r\n`)), "SMTP DATA write");
    const accepted = await readSmtpResponse(conn);
    if (accepted.code !== 250) {
      throw new Error(`SMTP ${accepted.code}: ${accepted.text.slice(0, 240)}`);
    }
    dataAccepted = true;
    try {
      await smtpCommand(conn, "QUIT", [221]);
    } catch {
      // Delivery was already accepted by Gmail; QUIT failure does not change delivery outcome.
    }
    return { status: "sent", providerId: message.messageId, error: "" };
  } catch (error) {
    const messageText = text(error) || "Gmail SMTP delivery failed.";
    if (dataStarted && !dataAccepted) {
      return {
        status: "uncertain",
        providerId: message.messageId,
        error: `Delivery outcome uncertain after SMTP DATA started: ${messageText}`,
      };
    }
    return { status: "failed", providerId: message.messageId, error: messageText };
  } finally {
    try {
      conn?.close();
    } catch {
      // Ignore socket-close errors.
    }
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
      email_provider: EMAIL_PROVIDER,
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

  const gmailConfigured = Boolean(
    isEmail(text(Deno.env.get("HEALTHYME_GMAIL_USER")))
    && text(Deno.env.get("HEALTHYME_GMAIL_APP_PASSWORD")).replace(/\s+/g, ""),
  );

  if (!gmailConfigured) {
    const { error: configMarkError } = await admin
      .from(EVENT_TABLE)
      .update({
        email_status: "configuration_missing",
        email_provider: EMAIL_PROVIDER,
        updated_at: now.toISOString(),
      })
      .eq("email_status", "pending");
    if (configMarkError) {
      console.warn("consultation-reminders: could not mark missing Gmail configuration", configMarkError.message);
    }
    console.warn("consultation-reminders: Gmail SMTP configuration is missing; reminders were staged but email was not attempted");
    return Response.json({ ok: true, eligible, created, emailed: 0, emailConfigured: false, provider: EMAIL_PROVIDER });
  }

  const { data: pendingRows, error: pendingError } = await admin
    .from(EVENT_TABLE)
    .select("*")
    .in("email_status", ["pending", "failed", "configuration_missing"])
    .lt("email_attempt_count", MAX_EMAIL_ATTEMPTS)
    .order("created_at", { ascending: true })
    .limit(8);
  if (pendingError) {
    console.error("consultation-reminders: pending delivery read failed", pendingError.message);
    return Response.json({ error: "Reminder delivery queue could not be read" }, { status: 500 });
  }

  let emailed = 0;
  let suppressed = 0;
  let failed = 0;
  let uncertain = 0;

  for (const raw of pendingRows ?? []) {
    const event = raw as ReminderEvent;
    const currentSchedule = scheduleById.get(text(event.schedule_id));
    if (!currentSchedule || !stageStillValid(event.stage, currentSchedule, new Date())) {
      await admin
        .from(EVENT_TABLE)
        .update({
          email_status: "suppressed",
          email_provider: EMAIL_PROVIDER,
          email_error: "Schedule is no longer eligible for this reminder stage.",
          updated_at: new Date().toISOString(),
        })
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
        email_provider: EMAIL_PROVIDER,
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
    const delivery = await sendGmailSmtp(deliveryEvent, memberName(state, currentSchedule));
    const completedAt = new Date().toISOString();
    const sent = delivery.status === "sent";

    if (delivery.status === "uncertain") {
      const { error: uncertainUpdateError } = await admin
        .from(EVENT_TABLE)
        .update({
          email_provider: EMAIL_PROVIDER,
          email_provider_id: delivery.providerId,
          email_error: delivery.error.slice(0, 500),
          updated_at: completedAt,
        })
        .eq("id", event.id)
        .eq("email_status", "sending");
      if (uncertainUpdateError) {
        console.error("consultation-reminders: uncertain delivery audit update failed", event.id, uncertainUpdateError.message);
      }
      uncertain += 1;
      continue;
    }

    const { error: updateError } = await admin
      .from(EVENT_TABLE)
      .update({
        email_status: delivery.status,
        email_provider: EMAIL_PROVIDER,
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
    provider: EMAIL_PROVIDER,
    eligible,
    created,
    emailed,
    suppressed,
    failed,
    uncertain,
    at: now.toISOString(),
  }));

  return Response.json({
    ok: true,
    eligible,
    created,
    emailed,
    suppressed,
    failed,
    uncertain,
    emailConfigured: true,
    provider: EMAIL_PROVIDER,
  });
});