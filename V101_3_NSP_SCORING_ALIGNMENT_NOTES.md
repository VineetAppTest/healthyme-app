# v101.3 NSP Scoring Excel Mapping Alignment

## Source of truth

- Uploaded workbook: `NSPform&Subform_xl-1 (1).xlsx`
- Page 1 mapping: non-grey cells in `NSP Client Assessment (Pg 1)` range `E6:N45`
- Page 2 mapping: non-grey cells in `NSP Client Assessment (Pg 2)` range `E7:N33`
- Answer values from Column C are copied into the non-grey mapped system cells.
- Section totals are the sum of Page 1 + Page 2 mapped values.
- App answer scoring remains: `1 = 1`, `2 = 2`, `3 = 3`, `NA/blank/Select = 0`.

## Expected totals from uploaded Excel sample

| Section | Old app mapped questions | Excel mapped questions | Expected sample total |
|---|---:|---:|---:|
| Digestive | 13 | 28 | 31 |
| Intestinal | 11 | 38 | 34 |
| Immune/Lymphatic | 11 | 26 | 23 |
| Nervous | 10 | 22 | 25 |
| Circulatory/Cardiovascular | 5 | 26 | 28 |
| Respiratory | 5 | 17 | 9 |
| Glandular/Endocrine | 10 | 34 | 43 |
| Reproductive | 5 | 20 | 21 |
| Urinary | 4 | 14 | 13 |
| Musculoskeletal | 6 | 14 | 11 |

## Summary of correction

The previous app logic was summing values correctly, but the question-to-system map was incomplete and not derived from the Excel non-grey cells. v101.3 replaces `config/systems_rating_map.json` with the Excel-derived mapping.

## Changed mapping detail

### Digestive
- Old mapped count: 13
- Excel-derived mapped count: 28
- Expected sample total: 31
- Added question mappings: nsp1_q1, nsp1_q2, nsp1_q4, nsp1_q6, nsp1_q9, nsp1_q13, nsp1_q16, nsp1_q24, nsp1_q26, nsp1_q35, nsp1_q37, nsp1_q39, nsp2_q44, nsp2_q53, nsp2_q58, nsp2_q61, nsp2_q62
- Removed old mappings not active in Excel: nsp2_q46, nsp2_q47

### Intestinal
- Old mapped count: 11
- Excel-derived mapped count: 38
- Expected sample total: 34
- Added question mappings: nsp1_q1, nsp1_q3, nsp1_q7, nsp1_q9, nsp1_q14, nsp1_q16, nsp1_q17, nsp1_q20, nsp1_q21, nsp1_q22, nsp1_q26, nsp1_q28, nsp1_q32, nsp1_q33, nsp1_q37, nsp2_q41, nsp2_q50, nsp2_q52, nsp2_q55, nsp2_q56, nsp2_q58, nsp2_q59, nsp2_q60, nsp2_q63, nsp2_q65, nsp2_q66, nsp2_q67
- Removed old mappings not active in Excel: None

### Immune/Lymphatic
- Old mapped count: 11
- Excel-derived mapped count: 26
- Expected sample total: 23
- Added question mappings: nsp1_q4, nsp1_q5, nsp1_q9, nsp1_q10, nsp1_q11, nsp1_q14, nsp1_q15, nsp1_q17, nsp1_q23, nsp1_q27, nsp1_q32, nsp1_q33, nsp2_q48, nsp2_q55, nsp2_q64
- Removed old mappings not active in Excel: None

### Nervous
- Old mapped count: 10
- Excel-derived mapped count: 22
- Expected sample total: 25
- Added question mappings: nsp1_q4, nsp1_q5, nsp1_q6, nsp1_q10, nsp1_q19, nsp1_q20, nsp1_q29, nsp1_q37, nsp1_q40, nsp2_q45, nsp2_q50, nsp2_q60, nsp2_q65
- Removed old mappings not active in Excel: nsp1_q30

### Circulatory/Cardiovascular
- Old mapped count: 5
- Excel-derived mapped count: 26
- Expected sample total: 28
- Added question mappings: nsp1_q1, nsp1_q2, nsp1_q4, nsp1_q5, nsp1_q6, nsp1_q10, nsp1_q14, nsp1_q17, nsp1_q18, nsp1_q25, nsp1_q26, nsp1_q27, nsp1_q28, nsp1_q30, nsp1_q40, nsp2_q42, nsp2_q43, nsp2_q48, nsp2_q57, nsp2_q59, nsp2_q63
- Removed old mappings not active in Excel: None

### Respiratory
- Old mapped count: 5
- Excel-derived mapped count: 17
- Expected sample total: 9
- Added question mappings: nsp1_q1, nsp1_q3, nsp1_q5, nsp1_q9, nsp1_q12, nsp1_q13, nsp1_q18, nsp1_q20, nsp1_q37, nsp1_q40, nsp2_q44, nsp2_q52
- Removed old mappings not active in Excel: None

### Glandular/Endocrine
- Old mapped count: 10
- Excel-derived mapped count: 34
- Expected sample total: 43
- Added question mappings: nsp1_q1, nsp1_q4, nsp1_q5, nsp1_q6, nsp1_q8, nsp1_q9, nsp1_q10, nsp1_q14, nsp1_q16, nsp1_q19, nsp1_q20, nsp1_q21, nsp1_q22, nsp1_q26, nsp1_q30, nsp1_q31, nsp1_q33, nsp1_q35, nsp1_q36, nsp1_q40, nsp2_q45, nsp2_q49, nsp2_q50, nsp2_q54, nsp2_q59
- Removed old mappings not active in Excel: nsp2_q63

### Reproductive
- Old mapped count: 5
- Excel-derived mapped count: 20
- Expected sample total: 21
- Added question mappings: nsp1_q10, nsp1_q12, nsp1_q16, nsp1_q18, nsp1_q20, nsp1_q21, nsp1_q22, nsp1_q25, nsp1_q33, nsp1_q35, nsp1_q38, nsp2_q51, nsp2_q53, nsp2_q58, nsp2_q59
- Removed old mappings not active in Excel: None

### Urinary
- Old mapped count: 4
- Excel-derived mapped count: 14
- Expected sample total: 13
- Added question mappings: nsp1_q3, nsp1_q6, nsp1_q9, nsp1_q12, nsp1_q17, nsp1_q38, nsp2_q55, nsp2_q57, nsp2_q61, nsp2_q63, nsp2_q64
- Removed old mappings not active in Excel: nsp2_q53

### Musculoskeletal
- Old mapped count: 6
- Excel-derived mapped count: 14
- Expected sample total: 11
- Added question mappings: nsp1_q1, nsp1_q2, nsp1_q5, nsp1_q6, nsp1_q17, nsp1_q18, nsp1_q19, nsp2_q49, nsp2_q59
- Removed old mappings not active in Excel: nsp2_q43
