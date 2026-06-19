# v102.3A — Supplement Validation + End-Date UAT Checklist

## Admin — Add Supplement

1. Add Supplement shows Start Date.
2. End Date appears directly under Start Date.
3. End Date is NA by default.
4. When Set End Date is selected, the End Date calendar defaults to the selected Start Date.
5. Member Instructions and Admin Notes appear adjacent to each other.
6. If Frequency says Once/Twice/Thrice or 1x/2x/3x, save is blocked unless Timing + Additional Timing count matches.
7. Additional Timing count includes comma/semicolon/pipe/line-break separated entries.
8. Save is blocked if End Date is earlier than Start Date.

## Admin — Edit Supplement

1. Edit Supplement has the same timing capabilities as Add Supplement.
2. Timing appears before Frequency.
3. Start Date and End Date appear adjacent to each other.
4. Start Date is placed to the left and End Date is placed to the right.
5. End Date is NA by default if no end date exists.
6. Frequency-vs-timing validation works the same as Add Supplement.
7. Member Instructions and Admin Notes appear adjacent to each other.

## Automatic Stop

1. When End Date is today or in the past, the supplement automatically moves from Active to Stopped.
2. Auto-stopped supplement disappears from Member view.
3. Auto-stopped supplement remains in Admin Stopped Supplements / History.
4. Stop reason is exactly: Predefined Timelines.

## History UI

1. Stopped Supplements / History uses + when collapsed.
2. Stopped Supplements / History uses - when expanded.
3. Previous stopped supplement records remain visible in history.

## Scope guard

1. No PDF/download has been added.
2. No Recommendations module has been added.
3. No meal-plan or exercise-plan integration has been added.
