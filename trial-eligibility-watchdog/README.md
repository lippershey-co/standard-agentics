# Trial-Eligibility-Watchdog

Track and review clinical trial eligibility criteria for possible screening or enrollment-impact signals.

## What it does

Trial-Eligibility-Watchdog accepts pasted eligibility criteria text and runs a deterministic review engine to surface possible first-pass screening, structure, or enrollment-impact issues.  
For eligible public-demo inputs, it can also generate an optional Claude-based AI summary that rewrites the deterministic findings into a plain-language reviewer note.

The tool also supports a structured **Trial identifier / NCT ID** field to anchor the review context.

## Current architecture

### 1. Deterministic review engine
This is the source of truth for the public demo.

It currently checks a starter set of rule families, including:
1. Trial identifier anchoring
2. Criteria structure completeness heuristics
3. Potential eligibility tightening or screening-impact terms
4. Performance status restriction detection
5. Potential CNS-related exclusion detection

### 2. Claude-based AI summary
This is an assistive layer only.

It:
- summarizes deterministic findings in plain English
- does not replace deterministic findings
- does not output PASS/FAIL
- does not determine trial feasibility or regulatory acceptability
- still requires human review

## Structured input

The public demo includes a structured field for:

- **Trial identifier / NCT ID**

This is used to strengthen review context and transparency outputs.

## Rule references shown in v1

- Structured metadata anchor
- Trial criteria structure heuristic
- Eligibility screening heuristic
- Eligibility population narrowing heuristic
- Eligibility exclusion heuristic

## Transparency & oversight

Trial-Eligibility-Watchdog can generate a stakeholder-facing **Transparency & Oversight Report** that describes:
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
- Trial eligibility / screening text only for AI summary
- No PDF or DOCX support in the public demo
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

Hybrid public demo working:
- deterministic review engine
- findings with risk levels
- structured trial-identifier input
- downloadable text report
- downloadable Transparency & Oversight Report
- optional Claude-based AI summary
- support CTA
- persistent state across reruns

## What this version does not do

- It does not determine trial feasibility
- It does not approve eligibility criteria
- It does not make final regulatory or protocol judgments
- It is not intended for production use

## Demo flow

1. Enter a trial identifier / NCT ID if relevant
2. Paste eligibility criteria text
3. Run the deterministic watchdog review
4. Review findings, risk level, and rule references
5. Generate an AI summary if the input is within demo limits
6. Download a text report or transparency report if needed

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
