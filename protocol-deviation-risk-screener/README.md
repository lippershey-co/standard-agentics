# Protocol-Deviation-Risk-Screener

Screen protocol-style text for visible deviation-risk patterns, operational ambiguity, and documentation gaps.

## What it does

Protocol-Deviation-Risk-Screener accepts pasted protocol, study-design, or nonclinical text and runs a deterministic deviation-risk engine to surface possible first-pass protocol-quality and governance risks.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic deviation-risk engine
This is the source of truth for the public demo.

It currently checks a starter set of deviation-risk heuristics:
1. Control-arm structure detection
2. Objective-endpoint alignment signal detection
3. Operational ambiguity detection
4. Deviation-handling language detection
5. Documentation / GLP signal detection
6. Deviation-risk table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and deviation-risk-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine formal GLP compliance, audit outcome, or final regulatory acceptability
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- deviation-risk logic used in the demo
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
- Protocol / study-design / deviation-risk review text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic deviation-risk engine
- risk-ranked findings
- deviation-risk table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine formal GLP compliance
- It does not determine audit outcome
- It does not determine final regulatory acceptability
- It does not make final legal, medical, clinical, audit, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste protocol or study-design text
2. Run the deterministic deviation-risk screen
3. Review findings and the deviation-risk table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
