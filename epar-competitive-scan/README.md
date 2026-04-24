# EPAR-Competitive-Scan

Extract structured competitive intelligence from EPAR-style text and generate a simple review table.

## What it does

EPAR-Competitive-Scan accepts pasted EPAR, EMA, or regulatory-intelligence text and runs a deterministic EPAR intelligence engine to surface possible first-pass competitive-review signals.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic EPAR intelligence engine
This is the source of truth for the public demo.

It currently checks a starter set of EPAR heuristics:
1. Indication detection
2. Clinical-efficacy package detection
3. Safety / risk detection
4. Regulatory-outcome detection
5. Post-authorisation obligation detection
6. EPAR intelligence table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and EPAR-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine strategic attractiveness or final competitive conclusions
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- EPAR intelligence logic used in the demo
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
- EPAR / EMA / regulatory-intelligence text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic EPAR intelligence engine
- risk-ranked findings
- EPAR intelligence table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine regulatory superiority
- It does not determine strategic attractiveness
- It does not determine final competitive position
- It does not make final legal, medical, regulatory, or commercial judgments
- It is not intended for production use

## Demo flow

1. Paste EPAR-style or regulatory-intelligence text
2. Run the deterministic EPAR scan
3. Review findings and the EPAR intelligence table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
