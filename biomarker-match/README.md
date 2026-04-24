# Biomarker-Match

Scan biomarker/pathology-style text for visible actionable markers and generate a simple match-review table.

## What it does

Biomarker-Match accepts pasted biomarker, molecular, or pathology-style text and runs a deterministic biomarker engine to surface possible first-pass actionable-marker signals.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic biomarker engine
This is the source of truth for the public demo.

It currently checks a starter set of biomarker heuristics:
1. Biomarker pattern detection
2. Negative / not-detected context handling
3. Tumor-type extraction from local context
4. Biomarker match table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and biomarker-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine medical eligibility, treatment selection, or final clinical action
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- matching logic used in the demo
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
- Biomarker / molecular / pathology-style text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic biomarker engine
- risk-ranked findings
- biomarker match table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine medical eligibility
- It does not determine treatment selection
- It does not determine trial qualification
- It does not make final legal, medical, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste biomarker, molecular, or pathology-style text
2. Run the deterministic biomarker check
3. Review findings and the biomarker match table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
