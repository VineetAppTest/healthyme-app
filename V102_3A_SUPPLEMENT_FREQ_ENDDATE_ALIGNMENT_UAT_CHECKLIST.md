# HealthyMe v102.3A — Supplement Frequency + End Date Alignment UAT Checklist

## Scope

This build is a narrow Admin Supplement Manager UX correction on top of v102.3A.

## Included

1. Add Supplement Frequency field is now a dropdown list from Once to Ten times.
2. Edit Supplement Frequency field is now a dropdown list from Once to Ten times.
3. Existing frequency values in Edit mode map to the correct dropdown option where possible.
4. Frequency validation continues to compare Frequency count against selected Timing plus Additional Timing entries.
5. Add Supplement places Set End Date and End Date / End Date: NA closer and adjacent.
6. Edit Supplement places Set End Date and End Date / End Date: NA closer and adjacent beside Start Date.

## Exclusions

- No PDF.
- No Recommendations module.
- No meal plan integration.
- No exercise plan integration.
- No report generation change.

## Test Cases

- Add Supplement: select Twice, choose Morning + Evening, save should pass.
- Add Supplement: select Twice, choose Morning only, save should show validation error.
- Add Supplement: select Thrice, choose Morning + Evening and add one Additional Timing, save should pass.
- Edit Supplement: Frequency should appear as dropdown, not free-text.
- Edit Supplement: Dosage and Frequency should remain adjacent.
- Edit Supplement: Timing and Additional Timing should remain adjacent.
- End Date unchecked should show End Date: NA close to Set End Date.
- End Date checked should show calendar close to Set End Date.
- Member view should remain active-only.
- Stopped history should remain available to Admin.
