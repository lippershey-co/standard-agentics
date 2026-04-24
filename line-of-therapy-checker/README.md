# Line-of-Therapy-Checker

Check promotional or medical content for line-of-therapy wording and sequencing-positioning inconsistencies.

## What it does

Line-of-Therapy-Checker accepts pasted promotional, medical, or positioning text and runs a deterministic positioning engine to surface possible first-pass line-of-therapy issues.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic positioning engine
This is the source of truth for the public demo.

It currently checks a starter set of positioning heuristics:
1. First-line wording detection
2. Later-line wording detection
3. Sequencing-context detection
4. Potential mismatch review between line-of-therapy wording and prior-treatment references
5. Positioning summary table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and positioning-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine label compliance or final medical/legal/regulatory acceptability
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- positioning logic used in the demo
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
- Promotional / medical / line-of-therapy positioning text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic positioning engine
- risk-ranked findings
- positioning table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine label compliance
- It does not determine promotional approval
- It does not make final legal, medical, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste promotional, medical, or positioning text
2. Run the deterministic line-of-therapy check
3. Review findings and the positioning table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
