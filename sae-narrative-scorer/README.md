# SAE-Narrative-Scorer

Review SAE narrative text for visible completeness elements before deeper safety review.

## What it does

SAE-Narrative-Scorer accepts pasted SAE or safety-case narrative text and runs a deterministic narrative-completeness engine to surface possible first-pass documentation gaps.

For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

## Current v1 architecture

### 1. Deterministic SAE narrative engine
This is the source of truth for the public demo.

It currently checks a starter set of completeness heuristics:
1. Patient-context detection
2. Event-description detection
3. Exposure / suspect-product context detection
4. Chronology / onset detection
5. Seriousness / outcome detection
6. Action-taken detection
7. Follow-up / rechallenge context detection
8. SAE completeness table generation

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings and SAE-completeness-table outputs in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine MedWatch/EudraVigilance submission readiness, medical causality, or final reporting adequacy
- still requires human review

### 3. Transparency & Oversight Report
The app can generate a downloadable PDF transparency report for stakeholders.

It describes:
- system identity
- deterministic vs AI summary roles
- SAE narrative logic used in the demo
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
- SAE / safety-case / narrative-review text only for AI summary
- No PDF or DOCX support for content inputs in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic SAE narrative engine
- risk-ranked findings
- SAE completeness table
- downloadable text report
- downloadable Transparency & Oversight Report (PDF)
- optional Claude-based AI summary
- formatted AI summary rendering
- Result Quality Review teaser
- support CTA

## What this version does not do

- It does not determine MedWatch/EudraVigilance submission readiness
- It does not determine medical causality
- It does not determine final reporting adequacy
- It does not make final legal, medical, clinical, pharmacovigilance, or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste SAE or safety-case narrative text
2. Run the deterministic SAE narrative review
3. Review findings and the SAE completeness table
4. Generate an AI summary if the input is within demo limits
5. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
