export type MemberLifecycleState =
  | "initial_assessment"
  | "under_review"
  | "active_plan"
  | "reassessment";

export type JourneyBucket = "now" | "next" | "later" | "done";

export type JourneyDomain =
  | "assessment"
  | "meal"
  | "supplement"
  | "exercise"
  | "consultation"
  | "message"
  | "log";

export type JourneyItem = {
  id: string;
  domain: JourneyDomain;
  bucket: JourneyBucket;
  title: string;
  detail?: string;
  timingLabel?: string;
  href?: string;
  actionLabel?: string;
  /**
   * True only when HealthyMe has an authoritative completion/acknowledgement
   * state. The presentation layer must never infer completion from elapsed time.
   */
  authoritativeDone?: boolean;
};

export type MemberJourneyModel = {
  lifecycle: MemberLifecycleState;
  memberLocalDateLabel: string;
  memberTimezone: string;
  primaryAction: JourneyItem | null;
  now: JourneyItem[];
  next: JourneyItem[];
  later: JourneyItem[];
  done: JourneyItem[];
};
