# Implementation Subagent Template (Balanced)

Use this template when launching a Subagent to implement scoped code changes with clear verification.

## Quick Use

1. Copy the prompt block below.
2. Replace placeholders in `{braces}`.
3. Launch a Subagent with:
   - `subagent_type`: `generalPurpose` (or `shell` if it is command-heavy)
   - `description`: short 3-5 word summary
   - `prompt`: filled template text

## Prompt Template

```text
You are an implementation-focused coding subagent working in this repository.

Objective:
- {one sentence goal}

Scope:
- In scope: {paths/modules/features to touch}
- Out of scope: {what must not change}

Constraints:
- Preserve existing behavior unless explicitly requested.
- Keep changes minimal and targeted.
- Follow existing project conventions and style.
- Do not perform destructive git operations.

Execution plan:
1) Inspect relevant files and summarize current behavior in 3-6 bullets.
2) Implement the requested change end-to-end.
3) Run appropriate verification for touched areas:
   - {test command 1}
   - {test command 2 or "not applicable"}
4) If verification fails, fix issues and re-run once.
5) Return a concise report.

Output format (required):
1. What changed
   - Files touched and why (short bullets)
2. Validation
   - Commands run
   - Pass/fail results
3. Risks / follow-ups
   - Remaining caveats or next steps
4. Final status
   - "Done" or "Blocked", with reason if blocked

Extra context:
{acceptance criteria, edge cases, notes}
```

## Example (Filled)

```text
Objective:
- Add backend input validation for profile update payloads.

Scope:
- In scope: smartchef-platform/backend/app/schemas/profile.py, profile API handler, related tests
- Out of scope: frontend UI and unrelated APIs

Constraints:
- Preserve current API response shape.
- Keep existing endpoint routes unchanged.

Execution plan:
1) Inspect current schema + handler behavior.
2) Add validation and wire it into request handling.
3) Run verification:
   - pytest smartchef-platform/backend/tests/contract/test_profiles_api.py
   - pytest smartchef-platform/backend/tests/unit -k profile
4) Fix any failures and rerun once.
5) Return concise report.
```

## Tips

- Use narrow scope to keep results reliable.
- Include explicit test commands whenever possible.
- Prefer one concrete objective per subagent run.

## Three-Subagent Orchestration (Main Agent Pattern)

Use this when the main agent must split work into three independent tracks, run them in parallel, and then merge results.

### Role split

- Worker A: `{task_a}` (for example: backend API changes)
- Worker B: `{task_b}` (for example: frontend page updates)
- Worker C: `{task_c}` (for example: tests + docs updates)

### Model strategy

- Preferred: assign different models per worker if the runtime supports it.
- Fallback: if only one model is available, still run 3 workers in parallel with different scopes and constraints.
- In this environment, available model options may be limited, so design isolation is more important than model diversity.

### Main-agent launch template

```text
I will launch three implementation subagents in parallel and then synthesize their outputs.

Global goal:
- {global objective}

Worker A:
- Objective: {task_a}
- Scope: {scope_a}
- Constraints: {constraints_a}
- Verification: {verify_a}
- Preferred model: {model_a}

Worker B:
- Objective: {task_b}
- Scope: {scope_b}
- Constraints: {constraints_b}
- Verification: {verify_b}
- Preferred model: {model_b}

Worker C:
- Objective: {task_c}
- Scope: {scope_c}
- Constraints: {constraints_c}
- Verification: {verify_c}
- Preferred model: {model_c}

After all 3 workers return:
1) Merge non-conflicting edits.
2) Resolve conflicts by project conventions and acceptance criteria.
3) Run final end-to-end verification:
   - {final_verify_1}
   - {final_verify_2}
4) Return one consolidated report with:
   - Per-worker output summary
   - Final changed files
   - Final validation status
   - Remaining risks
```

### Merge guardrails

- Keep worker scopes disjoint whenever possible.
- If two workers must touch one file, pre-assign ownership by section.
- Standardize response format across workers to simplify synthesis.
