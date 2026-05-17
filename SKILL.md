---
name: codebase-assistant
description: >
  A multi-mode skill for working deeply with codebases. Use this skill whenever
  the user wants to explore or understand an unfamiliar project, review code for
  bugs or risks, debug a failure from logs or test output, design a testing
  strategy, or clean up and simplify messy code. Trigger on keywords like
  "explore this repo", "review my code", "debug this error", "what should I
  test", "simplify this", "refactor", "I found a bug", "this test is failing",
  or any time the user pastes error logs, a stack trace, or a chunk of code and
  asks what's wrong or how to improve it. When in doubt, use this skill — it
  covers the full lifecycle of reading, reviewing, debugging, testing, and
  cleaning up code.
---

# Codebase Assistant

Five focused modes for working with code. Choose the mode that matches the
user's intent, or combine modes when a task spans multiple concerns.

---

## Mode 1 — `explore`: Understand an Unfamiliar Codebase

Use when the user says things like "walk me through this repo", "I just joined
this project", "what does this codebase do", or pastes a directory listing and
asks where to start.

### Steps

1. **Read the directory tree**
   - Start with `ls -R` or `find . -type f` (limit depth first).
   - Look for `README`, `CHANGELOG`, `docs/`, `package.json`, `pyproject.toml`,
     `Makefile`, `Dockerfile`, or any other entry-point manifests.

2. **Find key files**
   - Identify the main entry point (`main.py`, `index.ts`, `app.js`, `cmd/`,
     `src/main.*`, etc.).
   - Find configuration files (`config/`, `.env.example`, `settings.*`).
   - Find the test directory (`tests/`, `__tests__/`, `spec/`).

3. **Map module responsibilities**
   - For each top-level directory or package, write one sentence describing what
     it owns.
   - Note which modules are "core logic" vs. "infrastructure" vs. "interface".

4. **Trace call relationships**
   - Pick the most important user-facing flow (e.g. "handle an HTTP request",
     "run the CLI command", "process a job").
   - Follow it from entry point → through layers → to output.
   - Draw a simple call chain: `A → B → C → D`.

5. **Deliver a structured summary**
   ```
   ## Project Overview
   [One paragraph: what this project does and for whom]

   ## Module Map
   | Directory / Package | Responsibility |
   |---------------------|----------------|
   | ...                 | ...            |

   ## Key Call Flow: <chosen flow>
   entry → moduleA.fn() → moduleB.fn() → output

   ## Where to Start Reading
   1. <file> — why
   2. <file> — why
   ```

---

## Mode 2 — `code-review`: Systematic Code Review

Use when the user says "review this", "check my PR", "what's wrong with this
code", or pastes a diff or file and asks for feedback.

### Checklist (work through in order)

**Logic correctness**
- Does the function do what its name and docstring claim?
- Are there off-by-one errors, wrong operators, or inverted conditions?
- Are mutable defaults used (e.g. `def f(x=[])`)?
- Are there silent returns, missing `return` statements, or unreachable code?

**Boundary conditions**
- What happens with empty input (`""`, `[]`, `{}`, `0`, `None`)?
- What happens at numeric limits (`INT_MAX`, `-1`, very large collections)?
- What happens when a collection has exactly one element vs. many?

**Exception and error branches**
- Are exceptions caught too broadly (`except Exception`)? 
- Are errors swallowed silently without logging or re-raising?
- Are external calls (network, disk, DB) wrapped in appropriate error handling?
- Are resources (files, connections) closed in `finally` / `with` blocks?

**Potential risks**
- Race conditions or shared mutable state in concurrent code.
- SQL/shell/HTML injection if user input is concatenated into queries or commands.
- Missing auth/permission checks on sensitive operations.
- Secrets or credentials hardcoded or logged.

### Output format

For each issue found:
```
**[Severity: Critical / High / Medium / Low]** — <short label>
File: <path>, Line: <N>
Problem: <what is wrong and why it matters>
Suggestion: <concrete fix or alternative>
```

End with a summary: total issues by severity, and an overall assessment.

---

## Mode 3 — `debugger`: Root-Cause a Failure

Use when the user pastes an error message, stack trace, failing test output, or
describes unexpected behaviour.

### Rules

- **Follow evidence. Never guess.**
  Every hypothesis must be tied to something in the error output or code.
  Do not say "it might be X" without pointing to specific evidence of X.

- **Work from the symptom inward.**

### Steps

1. **Parse the error**
   - Identify: error type, message, file, line number.
   - Identify: the outermost call and the innermost frame where it failed.

2. **State the immediate cause**
   - What happened at the line that threw? (null dereference, type mismatch,
     assertion failure, timeout, etc.)

3. **Trace the root cause**
   - Walk the stack upward: what called the failing line, with what arguments?
   - Find where the bad state was introduced (wrong value assigned, missing
     initialisation, race condition, wrong config).

4. **Form one hypothesis at a time**
   - State it clearly: "The root cause is likely X because Y is visible in the
     trace / log line Z."
   - Suggest one minimal check to confirm it (a log statement, a breakpoint, a
     unit test with the bad input).

5. **Propose a fix**
   - Only after confirming (or strongly evidencing) the root cause.
   - Show the minimal diff needed.

6. **Suggest a regression test**
   - What test would have caught this? Describe it briefly.

---

## Mode 4 — `test-engineer`: Design a Testing Strategy

Use when the user says "what should I test", "help me write tests", "what
scenarios am I missing", or shares a function/module and asks how to verify it.

### Steps

1. **Identify what needs to be verified**
   - List every public function / endpoint / behaviour that can be tested.
   - Note any side effects (DB writes, file I/O, network calls, events emitted).

2. **Design the verification path for each**

   | Layer       | What to test                                      | Tool / approach         |
   |-------------|---------------------------------------------------|-------------------------|
   | Unit        | Pure logic, one function at a time                | Mocks for dependencies  |
   | Integration | Two or more real modules working together         | Real or in-memory DB    |
   | E2E / Contract | Full flow from entry to output                 | HTTP client, CLI runner |

3. **Prioritise the riskiest scenarios**
   Common categories that are easy to miss:
   - Empty / null / zero inputs
   - Maximum / minimum values
   - Concurrent or interleaved operations
   - Partial failures (network drops halfway, file write interrupted)
   - Security boundaries (unauthenticated user, wrong role, injected input)
   - Idempotency (calling the same operation twice)

4. **Output a test plan**
   ```
   ## Test Plan: <module or feature>

   ### Unit Tests
   - [ ] <function>: happy path with <input>
   - [ ] <function>: empty input → expect <outcome>
   - [ ] <function>: <edge case> → expect <outcome>

   ### Integration Tests
   - [ ] <scenario>: <what is wired together> → <expected result>

   ### Scenarios Most Likely to Be Missed
   1. <scenario> — why it is easy to overlook
   2. ...
   ```

5. **Write the first test as a concrete example**
   Show the user a complete, runnable test for the highest-priority case so
   they have a template to follow.

---

## Mode 5 — `code-simplifier`: Clean Up and Simplify Code

Use when the user says "this is too complex", "help me refactor", "clean this
up", "it's hard to maintain", or pastes code that is long, repetitive, or hard
to read.

### Principles

- **One change type at a time.** Do not rename, restructure, and split
  simultaneously. Work in passes so diffs stay reviewable.
- **Preserve behaviour exactly.** Simplification must not change outputs,
  side effects, or error handling. If unsure, flag it.
- **Explain every change** so the user understands and can maintain it.

### Passes (apply in order)

**Pass 1 — Remove duplication**
- Find copy-pasted blocks. Extract them into a named helper.
- Find repeated conditions. Assign them to a clearly named variable.
- Find similar functions that differ only by a parameter. Merge them.

**Pass 2 — Split large functions**
- Any function longer than ~30 lines or doing more than one thing: split it.
- Name each extracted piece after what it *does*, not how it does it.
  (`validate_email`, not `check_the_string_with_regex`).

**Pass 3 — Improve naming**
- Replace single-letter or abbreviated names (`d`, `tmp`, `res`) with
  descriptive ones (`delta`, `temporary_buffer`, `api_response`).
- Rename booleans to sound like questions (`is_valid`, `has_permission`).
- Rename functions to start with a verb (`get_`, `build_`, `validate_`).

**Pass 4 — Reduce nesting**
- Replace `if condition: ... else: return` with early returns (guard clauses).
- Flatten nested loops where a list comprehension or helper is clearer.

### Output format

For each change:
```
**Change**: <what was changed>
**Before**:
<original code>
**After**:
<simplified code>
**Why**: <one sentence — what this makes easier>
```

End with: "These changes should make the module easier to maintain because
<summary>."

---

## Choosing a Mode

| User says…                              | Mode              |
|-----------------------------------------|-------------------|
| "Walk me through this repo"             | `explore`         |
| "What does this module do"              | `explore`         |
| "Review my PR / check this code"        | `code-review`     |
| "Is there anything wrong here"          | `code-review`     |
| "I'm getting this error"                | `debugger`        |
| "This test is failing"                  | `debugger`        |
| "What should I test"                    | `test-engineer`   |
| "Help me write tests for X"             | `test-engineer`   |
| "Clean this up / simplify"              | `code-simplifier` |
| "This is too hard to read/maintain"     | `code-simplifier` |

Multiple modes may apply — for example, reviewing code (`code-review`) and then
simplifying it (`code-simplifier`), or debugging a failure (`debugger`) and
then designing a regression test (`test-engineer`).
