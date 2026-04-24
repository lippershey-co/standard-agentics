# Signal-Validation-Checklist

Check whether a pharmacovigilance signal assessment includes the expected validation elements and generate a simple review table.

## What it does

Signal-Validation-Checklist accepts pasted signal-assessment or pharmacovigilance review text and runs a deterministic signal-validation engine to surface possible first-pass methodological gaps.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic signal-validation engine
This is the source of truth for the public demo.

It currently checks a starter set of validation heuristics:
1. Signal description detection
2. Signal source / detection-context detection
3. Evidence-basis detection
4. Causality / plausibility detection
5. Alternative-explanations / confounders detection
6. Next-step / action detection
7. Signal-validation table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and signal-validation-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine clinical significance, regulatory significance, or final signal disposition
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- signal-validation logic used in the demo
- human oversight expectations
- public-demo limits
- data-handling cautions

### 4. Result Quality Review
The app includes a Result Quality Review teaser.

In the public version, this acts as a Private Pilot teaser for:
- case-specific result assessment
- what the tool handled well
- confidence and limitations review
- detailed missed-issue analysis
- case-specific improvement recommendations
- structured edge-case logging

## Public demo limits

- English only
- Paste plain text only
- Deterministic review up to 12,000 characters
- AI summary limited to 3,500 characters
- Pharmacovigilance / signal-assessment / signal-validation text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic signal-validation engine
- risk-ranked findings
- signal-validation table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine clinical significance
- It does not determine regulatory significance
- It does not determine final signal disposition
- It does not make final legal, medical, clinical, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste signal-assessment or pharmacovigilance review text
2. Run the deterministic signal-validation check
3. Review findings and the signal-validation table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
