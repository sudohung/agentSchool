---
name: continuous-code-review
description: >
  Perform iterative code review with a code → review → log fixList → fix → review loop.
  Use when the user asks to review code, improve code quality, fix issues found by review,
  or do a multi-pass code audit. Also triggers when the user says "review my code",
  "check for bugs", "code quality audit", "find issues", or wants to systematically
  improve code through repeated review cycles.
disable-model-invocation: false
---

# Continuous Code Review Skill

A self-iterating code review workflow. Each round invokes this skill itself for the next iteration, creating a continuous improvement loop until no new issues are found or max iterations (5) is reached.

## The Loop

```
code → review → log fixList → fix → review → ...
```

## Step 1: Read All Code

Read every source file in the target directory. Use parallel reads. Focus on:
- All source files (`.py`, `.ts`, `.js`, `.go`, `.rs`, etc.)
- Configuration files and entry points
- Module boundaries and `__init__.py` / `index` files

If the user specified a directory, use that. Otherwise, infer from context or ask.

## Step 2: Code Review

Perform a thorough multi-dimensional review. Check for:

### Critical (P0)
- **Runtime errors**: undefined references, broken imports, type mismatches that will crash
- **Security vulnerabilities**: path traversal, injection, exposed secrets, missing auth
- **Logic bugs**: incorrect conditions, missing branches, race conditions
- **Regression bugs**: previous fixes that broke something else

### High (P1)
- **Unused imports and dead code**: imports never referenced, functions never called
- **Missing error handling**: uncaught exceptions, silent failures
- **Resource leaks**: unclosed files, sessions, connections
- **Incorrect API usage**: wrong parameters, missing required fields

### Medium (P2)
- **Inconsistent code style**: mixed conventions within the same project
- **Missing or incorrect type annotations**: bare `list` instead of `list[T]`, missing `Optional`
- **Hardcoded values**: magic numbers, strings that should be configurable
- **Performance issues**: N+1 queries, missing caching, redundant operations, no connection pooling
- **Logging gaps**: unhandled exceptions without logging, silent `except: pass`

### Low (P3)
- **Import path inconsistencies**: same module imported different ways across files
- **Over-exposed internal APIs**: internal functions exported in `__init__.py`
- **Orphaned files**: no references anywhere in the codebase
- **Documentation gaps**: missing docstrings on public APIs

## Step 3: Log Issues to fixList.md

Write findings to `{project_root}/docs/fixList.md`. **Append to the existing file, never overwrite previous rounds.**

Use this structure for each issue:

```markdown
### FIX-NNN: Short descriptive title

**File**: `path/to/file.py:line`

**Problem**: Clear description of what's wrong and why it matters.

**Fix**: Concrete description of how to fix it.
```

At the bottom, maintain a checklist:

```markdown
### Round N
- [ ] FIX-NNN: Short description
- [ ] FIX-NNN: Short description
```

Rules:
- Sequential numbering across all rounds (FIX-001, FIX-002, ...)
- Always include file path and line number
- Categorize by priority in the review output (P0/P1/P2/P3)
- Mark checklist items as `[ ]` for pending, `[x]` for fixed

## Step 4: Fix Issues

Fix all issues from the fixList, working from P0 to P3:
- Make minimal, targeted changes — do not refactor beyond what's needed
- Preserve existing code conventions
- Do not introduce new functionality unless it's a direct fix
- After each fix, verify the change doesn't break anything (check imports, references)

## Step 5: Update Checklist

Mark all fixed items as `[x]` in the fixList.md checklist.

## Step 6: Self-Invoke for Next Round

After fixing, read all modified files again and check:
1. Are previous fixes correct and complete?
2. Did any fix introduce a regression?
3. Were any issues missed in previous rounds?
4. Are there new issues created by the fixes?
5. Apply agent SKILLS @continuous-code-review to review code.

If any issues are found, log them as new FIX-NNN entries and repeat from Step 4.

## Termination Conditions

The loop stops when:
- **No new issues** are found in a review round
- **Max iterations (5)** is reached
- **Only P3-level issues** remain (style/cosmetic only)

## Output Format

After each round, provide a summary:

```
## Round N Summary

| Fix | Priority | Status | Description |
|-----|----------|--------|-------------|
| FIX-001 | P0 | ✅ | Description |
| FIX-002 | P1 | ✅ | Description |

Total issues found: X | Fixed: Y | Remaining: Z
```

## Important Rules

1. **Never skip the fixList logging step** — every issue must be documented before fixing
2. **Always fix from highest priority to lowest** — P0 first, then P1, P2, P3
3. **Always re-check previous fixes for regressions** — a fix that breaks something else is worse than no fix
4. **The skill must call itself for the next round** — do not break the chain
5. **Stop after 5 rounds maximum** to avoid infinite loops
6. **Each round must read all relevant files fresh** — never rely on cached context from previous rounds
7. **Keep fixes minimal** — if a fix requires rewriting a whole module, note it as a recommendation rather than making the change