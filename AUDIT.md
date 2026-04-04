# video-to-article audit v1

## Scope

Review the current hamster video-to-article skill for trigger quality, skill portability, structure, and execution robustness.

## Findings

### High priority

1. Frontmatter is overloaded with non-core fields.
2. Description is feature-oriented but under-specifies trigger situations.
3. Core workflow and deployment-specific Notion/Cloudinary details are mixed together.
4. Secrets and environment-bound values were embedded in the skill.
5. Review-first behavior was missing from the operational workflow.

### Medium priority

6. Persona-specific rules are mixed into what looks like a reusable skill.
7. Step boundaries are improved but still need clearer separation of concerns.
8. Failure and fallback branches are underspecified.

### Lower priority

9. Some rules are written as fixes, not reusable design principles.
10. Repo structure should support references-first expansion.

## Optimization plan

### Phase 1
- sanitize secrets
- reduce frontmatter to spec-friendly fields
- strengthen description triggers
- split large deployment-specific sections into references

### Phase 2
- refine failure branches
- define the boundary as reusable core workflow + optional hamster deployment profile
- add example triggers, non-triggers, and outcome patterns

### Phase 3
- add minimal example assets for trigger clarity and output validation
- prepare the repo for packaging and validation once the structure stabilizes
