# Protocol-Amendment-Impact-Analyzer

Compare old vs new protocol-style text and surface likely amendment impacts on eligibility, safety, assessments, and endpoints.

## What it does

Protocol-Amendment-Impact-Analyzer accepts pasted old and new protocol text and runs a deterministic amendment-impact engine to surface possible first-pass operational and regulatory impact signals.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic amendment-impact engine
This is the source of truth for the public demo.

It currently checks a starter set of amendment-impact heuristics:
1. Eligibility-criteria change detection
2. Safety-reporting change detection
3. Assessment-schedule change detection
4. Endpoint-hierarchy change detection
5. Amendment-impact table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and amendment-impact-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine formal amendment classification, ethics requirements, or final regulatory obligations
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- amendment-impact logic used in the demo
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
- Deterministic review up to 12,000 characters per text box
- AI summary limited to 3,500 combined characters
- Protocol / amendment comparison text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic amendment-impact engine
- risk-ranked findings
- amendment-impact table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine formal amendment classification
- It does not determine ethics submission requirements
- It does not determine final regulatory obligations
- It does not make final legal, medical, clinical, ethics, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste old protocol text
2. Paste new protocol text
3. Run the deterministic amendment-impact review
4. Review findings and the amendment-impact table
5. Generate an AI summary if the input is within demo limits
6. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
