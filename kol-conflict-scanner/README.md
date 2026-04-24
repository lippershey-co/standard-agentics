# KOL-Conflict-Scanner

Review KOL-related text for visible disclosure, relationship, and conflict-alignment signals.

## What it does

KOL-Conflict-Scanner accepts pasted KOL, speaker, advisory, or disclosure-related text and runs a deterministic conflict-review engine to surface possible first-pass disclosure or alignment issues.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic conflict-review engine
This is the source of truth for the public demo.

It currently checks a starter set of conflict-review heuristics:
1. Relationship-disclosure context detection
2. Comparative / positioning signal detection
3. Content-company overlap detection
4. Disclosure completeness signal detection
5. Conflict-review table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and conflict-review-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine legal conflict status, compliance approval, or final speaker eligibility
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- conflict-review logic used in the demo
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
- KOL / speaker / disclosure / conflict-review text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic conflict-review engine
- risk-ranked findings
- conflict-review table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine legal conflict status
- It does not determine compliance approval
- It does not determine final speaker eligibility
- It does not make final legal, medical, compliance, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste KOL, speaker, advisory, or disclosure-related text
2. Run the deterministic conflict scan
3. Review findings and the conflict-review table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
