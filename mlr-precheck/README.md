# MLR-PreCheck

Review promotional text for possible medical, legal, and regulatory risk signals.

## What it does

MLR-PreCheck accepts pasted promotional text and runs a deterministic rules engine to surface possible first-pass review issues.  
For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language review note.

The tool also supports a structured **Approved indication / labeled setting** field to anchor conflict checks against the promotional body text.

## Current architecture

### 1. Deterministic review engine
This is the source of truth for the public demo.

It currently checks a growing starter set of rule families, including:
1. Benefit claim without visible risk language nearby
2. Absolute, superlative, or superiority promotional language
3. Implied comparative or superiority framing
4. Potential indication mismatch or off-label use framing
5. Statistically underpowered or weak evidence framing
6. Safety language may be present but fair balance may be insufficient

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine compliance
- still requires human review

## Structured input

The public demo includes a structured field for:

- **Approved indication / labeled setting**

This is used to strengthen conflict detection between:
- user-provided labeled setting
- promotional body text

## Rule references shown in v1

- FDA 21 CFR Part 202
- EU Directive 2001/83/EC Articles 87 and 89

## Transparency & oversight

MLR-PreCheck can generate a stakeholder-facing **Transparency & Oversight Report** that describes:
- system identity
- deterministic vs AI roles
- human oversight expectations
- public-demo limits
- data-handling cautions
- support contact

This transparency artifact is **not** a declaration of conformity and **not** a legal approval.

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

Hybrid public demo working:
- deterministic rules engine
- findings with risk levels
- rule references
- structured approved-indication input
- downloadable text report
- downloadable Transparency & Oversight Report
- optional Claude-based AI summary
- support CTA
- persistent state across reruns

## What this version does not do

- It does not perform a full MLR review
- It does not determine compliance
- It does not make final legal or regulatory judgments
- It is not intended for production use

## Demo flow

1. Enter the approved indication / labeled setting if relevant
2. Paste promotional text
3. Run the deterministic pre-check
4. Review findings, risk level, and rule references
5. Generate an AI summary if the input is within demo limits
6. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
