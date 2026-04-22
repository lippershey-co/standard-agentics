# Trial-Eligibility-Watchdog

Track and review clinical trial eligibility criteria changes.

## What it does

Trial-Eligibility-Watchdog is intended to help users review trial eligibility inputs by accepting either:

- one ClinicalTrials.gov NCT ID
- or one pasted eligibility criteria text block

## Current public demo scope

- English only
- No PDF support in v1
- One NCT ID or one pasted text block only
- Maximum 12,000 characters for pasted text
- No confidential, patient, or business-sensitive data
- Human review required

## Current status

v1 input and validation skeleton working.

## What this version does not do

- It does not yet fetch live ClinicalTrials.gov records
- It does not yet compare historical criteria versions
- It does not determine patient eligibility
- It is not intended for production use

## Demo flow

1. Enter an NCT ID or paste eligibility criteria text
2. Run the check
3. Review the input preview and validation message

## Not for production use

This tool is intended for evaluation and testing only.
For larger or more complex workflows, contact Lippershey.
