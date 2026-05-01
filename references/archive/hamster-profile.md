# Hamster Deployment Profile

Use this reference only when the skill is being executed for hamster's current publishing workflow.

## Purpose

Keep hamster-specific persona and publishing conventions separate from the reusable extraction workflow.

## Hamster-specific output conventions

- Publishing context may target hamster-branded knowledge outputs.
- Reflection fields may use a first-person hamster voice if the destination expects it.
- Internal sections intended only for Discord review should not leak into the final CMS body.

## Current destination assumptions

These are deployment assumptions, not universal skill rules:
- Notion is a common destination.
- Lead visual and reflection fields may exist.
- Some downstream property names are specific to hamster's current workspace.

## Usage rule

If the task is generic video-to-article conversion, do not load this file.
If the task explicitly targets hamster's publishing flow, load this file in addition to the core references you need.
