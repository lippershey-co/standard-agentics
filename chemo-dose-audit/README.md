# Chemo-Dose-Audit

Review chemotherapy dose-adjustment text for visible audit signals, rationale documentation, and protocol-reference clarity.

## What it does

Chemo-Dose-Audit accepts pasted chemotherapy dose-adjustment or regimen-review text and runs a deterministic dose-audit engine to surface possible first-pass documentation and traceability issues.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic chemotherapy dose-audit engine
This is the source of truth for the public demo.

It currently checks a starter set of dose-audit heuristics:
1. Regimen identification detection
2. Dose reduction / omission detection
3. Treatment delay detection
4. Toxicity-based rationale detection
5. Renal / hepatic documentation signal detection
6. Protocol-reference ambiguity detection
7. Chemo dose-audit table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and chemo-dose-audit-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine final dosing correctness, medical appropriateness, or protocol compliance
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- chemo dose-audit logic used in the demo
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
- Chemotherapy dose-adjustment / regimen-review / protocol-audit text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic chemotherapy dose-audit engine
- risk-ranked findings
- chemo dose-audit table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine final dosing correctness
- It does not determine medical appropriateness
- It does not determine protocol compliance
- It does not make final legal, medical, clinical, pharmacy, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste chemotherapy dose-adjustment text
2. Run the deterministic chemo dose audit
3. Review findings and the chemo dose-audit table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
