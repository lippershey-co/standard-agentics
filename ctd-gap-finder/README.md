# CTD-Gap-Finder

Audit a CTD package summary for possible missing or incomplete section coverage before formal submission review.

## What it does

CTD-Gap-Finder accepts pasted package-summary text and runs a deterministic completeness engine to surface possible first-pass CTD gaps.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic completeness engine
This is the source of truth for the public demo.

It currently checks a starter set of CTD areas:
1. Module 1 administrative documentation
2. Module 2 summary documentation
3. Module 3 CMC content
4. Container closure documentation
5. Stability package
6. Module 4 nonclinical content
7. Module 5 clinical content
8. Submission timing / readiness statement

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine submission adequacy
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- readiness logic used in the demo
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
- CTD / submission-readiness text only for AI summary
- No PDF or DOCX support for package inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic completeness engine
- findings with Present / Partial / Missing status
- readiness score
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine CTD adequacy
- It does not determine regulatory acceptability
- It does not make final legal, medical, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste a CTD or submission package summary
2. Run the deterministic gap check
3. Review findings, status, and recommended next actions
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
