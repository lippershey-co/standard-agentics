# Target-Landscape-Scanner

Scan oncology target-landscape notes for visible target activity and produce a simple ranked review table.

## What it does

Target-Landscape-Scanner accepts pasted landscape-summary text and runs a deterministic scan engine to surface visible target activity.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic scan engine
This is the source of truth for the public demo.

It currently checks a starter set of target-activity heuristics:
1. Target alias detection
2. Evidence-snippet extraction
3. Tumor-type extraction from local context
4. Ranked target activity table

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine scientific validity, strategic attractiveness, or competitive priority
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- landscape logic used in the demo
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
- Discovery / pipeline / target-landscape text only for AI summary
- No PDF or DOCX support for landscape inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic scan engine
- target activity findings
- ranked target activity table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine scientific validity
- It does not determine strategic attractiveness
- It does not determine competitive priority
- It does not make final legal, medical, scientific, or commercial judgments
- It is not intended for production use

## Demo flow

1. Paste a target-landscape or discovery scan summary
2. Run the deterministic landscape scan
3. Review findings and the target activity table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
