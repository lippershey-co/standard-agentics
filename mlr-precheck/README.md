# MLR-PreCheck

Review promotional text for possible medical, legal, and regulatory risk signals.

## What it does

MLR-PreCheck accepts pasted promotional text and runs a deterministic rules engine to surface possible first-pass review issues.  
For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language review note.

## Current v1 architecture

### 1. Deterministic review engine
This is the source of truth for the public demo.

It currently checks a narrow starter set of patterns:
1. Benefit claim without visible risk language nearby
2. Absolute or superlative promotional language
3. Potential off-label-looking population or indication language
4. Missing cautionary language trigger

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine compliance
- still requires human review

## Rule references shown in v1

- FDA 21 CFR Part 202
- EU Directive 2001/83/EC Articles 87 and 89

## Public demo limits

- English only
- Paste plain text only
- Deterministic review up to 12,000 characters
- AI summary limited to 3,500 characters
- Oncology promotional / claim-review text only for AI summary
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 hybrid demo working:
- deterministic rules engine
- findings with risk levels
- rule references
- downloadable text report
- optional Claude-based AI summary
- support CTA

## What this version does not do

- It does not perform a full MLR review
- It does not determine compliance
- It does not make final legal or regulatory judgments
- It is not intended for production use

## Demo flow

1. Paste promotional text
2. Run the deterministic pre-check
3. Review findings, risk level, and rule references
4. Generate an AI summary if the input is within demo limits
5. Download a text report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
