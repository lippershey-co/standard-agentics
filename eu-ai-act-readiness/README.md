# EU-AI-Act-Readiness

Assess an AI use case against a limited public-demo readiness workflow.

## What it does

EU-AI-Act-Readiness accepts a pasted AI use-case description and runs a limited deterministic checklist engine to surface possible readiness gaps.

The current demo supports:
- pasted text input
- input validation
- sample input loading
- reset behavior
- readiness results display
- reference areas
- downloadable text report
- Present / Partial / Missing scoring

## Current v1 checklist scope

This version checks these 9 readiness areas:

1. Human oversight
2. Risk management
3. Data governance
4. Technical documentation
5. Logging / record-keeping
6. Transparency / instructions for use
7. Accuracy / robustness / validation / monitoring
8. Quality management / governance process
9. Post-market monitoring / incident handling

## Scoring model

- **Present** = strong evidence detected
- **Partial** = weaker or indirect evidence detected
- **Missing** = no clear evidence detected

Readiness score:
- Present = 1.0
- Partial = 0.5
- Missing = 0.0

## Reference areas shown in v1

- EU AI Act — Human Oversight
- EU AI Act — Risk Management
- EU AI Act — Data Governance
- EU AI Act — Technical Documentation
- EU AI Act — Logging / Record-Keeping
- EU AI Act — Transparency / Instructions for Use
- EU AI Act — Accuracy, Robustness, Validation, Monitoring
- EU AI Act — Quality Management / Governance Process
- EU AI Act — Post-Market Monitoring / Incident Handling

## Current public demo scope

- English only
- Paste text only in this demo step
- No PDF or DOCX support yet
- Maximum 12,000 characters
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 deterministic checklist-engine demo working.

## What this version does not do

- It does not make a legal determination
- It does not definitively classify compliance or non-compliance
- It does not parse PDFs in the public demo
- It is not intended for production use

## Demo flow

1. Paste an AI use-case description
2. Run the readiness check
3. Review readiness results and reference areas
4. Download a text report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
