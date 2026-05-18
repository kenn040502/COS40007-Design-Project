---
name: codebase-assistant
description: >
  A multi-mode skill for working deeply with codebases. Use this skill whenever
  the user wants to explore or understand an unfamiliar project, review code for
  bugs or risks, debug a failure from logs or test output, design a testing
  strategy, clean up and simplify messy code, or audit security vulnerabilities.
  Trigger on keywords like "explore this repo", "review my code", "debug this
  error", "what should I test", "simplify this", "refactor", "I found a bug",
  "this test is failing", "check for security issues", or any time the user
  pastes error logs, a stack trace, or a chunk of code and asks what's wrong or
  how to improve it. When in doubt, use this skill — it covers the full
  lifecycle of reading, reviewing, debugging, testing, cleaning up, and
  securing code.
---

# Codebase Assistant

Six focused modes for working with code. Choose the mode that matches the
user's intent, or combine modes when a task spans multiple concerns.

---

## Mode 1 — `explore`: Understand an Unfamiliar Codebase

Use when the user says things like "walk me through this repo", "I just joined
this project", "what does this codebase do", or pastes a directory listing and
asks where to start.

### Steps

1. **Read the Directory — Project Map**
   - Run `ls -R` or `find . -type f --max-depth 3` to build a directory map.
   - Read `README`, `CHANGELOG`, `docs/`, `package.json`, `pyproject.toml`,
     `Makefile`, `Dockerfile`, or any entry-point manifests.
   - Produce a top-level map: what lives where, at a glance.

2. **Find Key Files — Entry Points and Core Files**
   - Identify the main entry point (`main.py`, `index.ts`, `app.js`, `cmd/`,
     `src/main.*`, etc.).
   - Find configuration files (`config/`, `.env.example`, `settings.*`).
   - Find the test directory (`tests/`, `__tests__/`, `spec/`).
   - Flag any file that is imported by many others — it is likely load-bearing.

3. **Map Module Responsibilities**
   - For each top-level directory or package, write one sentence describing
     what it owns.
   - Label each module as one of: `core logic` / `infrastructure` / `interface`
     / `utilities` / `config`.

4. **Trace Call Relationships — Call Chain**
   - Pick the most important user-facing flow (e.g. "handle an HTTP request",
     "run the CLI command", "process a job").
   - Trace it from entry point through layers to output.
   - Express as a call chain: `A → B.fn() → C.fn() → output`.

5. **Deliver a structured summary**
   ```
   ## Project Overview
   [One paragraph: what this project does and for whom]

   ## Module Map
   | Directory / Package | Type        | Responsibility |
   |---------------------|-------------|----------------|
   | ...                 | core logic  | ...            |

   ## Key Call Flow: <chosen flow>
   entry → moduleA.fn() → moduleB.fn() → output

   ## Where to Start Reading
   1. <file> — why
   2. <file> — why
   ```

---

## Mode 2 — `code-review`: Systematic Code Review

Use when the user says "review this", "check my PR", "what's wrong with this
code", or pastes a diff or file and asks for feedback. Run this checklist before
every commit.

### Checklist

**Logic Bugs**
- Does the function do what its name and docstring claim?
- Are there off-by-one errors, wrong operators, or inverted conditions?
- Are mutable defaults used (e.g. `def f(x=[])`)?
- Are there silent returns, missing `return` statements, or unreachable code?

**Boundary Conditions**
- What happens with empty input (`""`, `[]`, `{}`, `0`, `None`)?
- What happens at numeric limits (`INT_MAX`, `-1`, very large collections)?
- What happens when a collection has exactly one element?

**Exception Branches**
- Are exceptions caught too broadly (`except Exception`)?
- Are errors swallowed silently without logging or re-raising?
- Are external calls (network, disk, DB) wrapped in appropriate error handling?
- Are resources (files, connections) closed in `finally` / `with` blocks?

**Regression Risk**
- Does this change touch shared utilities or base classes that other modules
  depend on?
- Could this silently break callers that rely on the old behaviour?
- Is there a test that would catch a regression here? If not, flag it.

### Output format

For each issue found:
```
**[Severity: Critical / High / Medium / Low]** — <short label>
File: <path>, Line: <N>
Problem: <what is wrong and why it matters>
Suggestion: <concrete fix or alternative>
```

End with a summary: total issues by severity, overall assessment, and any
regression risks to watch.

---

## Mode 3 — `debugger`: Root-Cause a Failure

Use when the user pastes an error message, stack trace, failing test output, or
describes unexpected behaviour.

### Rules

- **Follow evidence. Never guess.**
  Every hypothesis must be tied to something in the error output or code.

### Steps

1. **Reproduce the Failure**
   - Ask for (or identify from context): exact steps to reproduce, environment,
     inputs used.
   - Confirm whether the failure is consistent or intermittent.

2. **Read the Error Logs**
   - Parse: error type, message, file, line number.
   - Identify the outermost call and the innermost frame where it failed.
   - Highlight any log lines that appear immediately before the crash.

3. **Locate the Root Cause**
   - Walk the stack upward: what called the failing line, with what arguments?
   - Find where the bad state was introduced (wrong value, missing init, race
     condition, wrong config).
   - State the root cause clearly: "The root cause is X because Y is visible at
     line Z."

4. **Minimal Fix**
   - Propose the smallest possible diff that fixes the root cause.
   - Do not refactor or improve unrelated code in the same fix.
   - Show the minimal diff, then suggest a regression test that would have
     caught this.

---

## Mode 4 — `test-engineer`: Design a Testing Strategy

Use when the user says "what should I test", "help me write tests", "what
scenarios am I missing", or shares a function/module and asks how to verify it.

### Steps

1. **Design the Verification Path — Critical Paths**
   - List every public function / endpoint / behaviour that can be tested.
   - Note side effects (DB writes, file I/O, network calls, events emitted).
   - For each, define the verification layer:

   | Layer       | What to test                                      | Tool / approach         |
   |-------------|---------------------------------------------------|-------------------------|
   | Unit        | Pure logic, one function at a time                | Mocks for dependencies  |
   | Integration | Two or more real modules working together         | Real or in-memory DB    |
   | E2E         | Full flow from entry to output                    | HTTP client, CLI runner |

2. **Regression Locations**
   - Identify where regressions are most likely: shared utilities, frequently
     changed modules, code with many callers.
   - Flag any existing gap where a test does not exist but should.

3. **Most Valuable Tests to Add**
   Prioritise the scenarios most likely to be missed:
   - Empty / null / zero inputs
   - Maximum / minimum values
   - Partial failures (network drops halfway, file write interrupted)
   - Idempotency (calling the same operation twice)
   - Security boundaries (unauthenticated user, wrong role, injected input)

4. **Output a test plan**
   ```
   ## Test Plan: <module or feature>

   ### Unit Tests
   - [ ] <function>: happy path with <input>
   - [ ] <function>: empty input → expect <outcome>
   - [ ] <function>: <edge case> → expect <outcome>

   ### Integration Tests
   - [ ] <scenario>: <what is wired together> → <expected result>

   ### Most Valuable Tests to Add
   1. <scenario> — why it is easy to overlook
   ```

5. Write the first test as a complete, runnable example so the user has a
   template to follow.

---

## Mode 5 — `code-simplifier`: Clean Up and Simplify Code

Use when the user says "this is too complex", "help me refactor", "clean this
up", or pastes code that is long, repetitive, or hard to read.

### Principles

- One change type per pass — do not rename, restructure, and split at the same
  time.
- Preserve behaviour exactly. Flag anything that might change a side effect.
- Explain every change so the user can maintain it going forward.

### Passes (apply in order)

**Remove Duplicate Logic**
- Find copy-pasted blocks and extract them into a named helper.
- Find repeated conditions and assign them to a clearly named variable.
- Merge similar functions that differ only by a parameter.

**Split Large Functions**
- Any function longer than ~30 lines or doing more than one thing: split it.
- Name each extracted piece after what it *does*
  (`validate_email`, not `check_string`).

**Tidy Naming**
- Replace single-letter or abbreviated names with descriptive ones.
- Rename booleans to sound like questions (`is_valid`, `has_permission`).
- Rename functions to start with a verb (`get_`, `build_`, `validate_`).
- Replace early-exit guard clauses to reduce nesting depth.

**Make the Project Easier to Maintain**
- After all passes, verify: could a new engineer read this in 5 minutes?
- Note any remaining complexity that is *inherent* (not accidental) and should
  be documented rather than removed.

### Output format

For each change:
```
**Change**: <what was changed>
**Before**: <original code>
**After**: <simplified code>
**Why**: <one sentence — what this makes easier>
```

---

## Mode 6 — `security-review`: Security Audit

Use when the user says "check for security issues", "is this safe", "audit this
code", or before any feature touching auth, payments, file uploads, or user
data ships.

### Checklist

**Authentication and Permissions**
- Are all sensitive routes protected by authentication middleware?
- Are authorisation checks performed on the server, not just the client?
- Are session tokens short-lived, rotated on login, and invalidated on logout?
- Is there protection against brute-force (rate limiting, lockout)?
- Are permission checks consistent — no endpoint that assumes a caller is
  authorised without verifying?

**Secrets and Uploads**
- Are secrets and API keys stored in environment variables or a secrets manager
  — never hardcoded or committed?
- Are uploaded files validated for type, size, and content (not just extension)?
- Are uploaded files stored outside the web root, or in object storage — never
  in a location that allows direct execution?
- Is there protection against path traversal (`../`) in file handling?

**Payments and User Data**
- Are payment amounts and totals verified server-side — never trusted from the
  client?
- Is sensitive user data (passwords, tokens, PII) encrypted at rest and in
  transit?
- Are passwords hashed with a modern algorithm (`bcrypt`, `argon2`) — never
  plain or MD5/SHA1?
- Is user input sanitised before being used in SQL queries, shell commands, or
  HTML output (SQL injection, XSS, command injection)?
- Is PII access logged and restricted to only the roles that need it?

### Output format

For each issue found:
```
**[Severity: Critical / High / Medium / Low]** — <short label>
Area: <auth / secrets / uploads / payments / data>
File: <path>, Line: <N> (if known)
Risk: <what an attacker could do>
Fix: <concrete remediation>
```

End with an overall risk rating and the top three fixes to prioritise.

---

## Choosing a Mode

| User says…                              | Mode               |
|-----------------------------------------|--------------------|
| "Walk me through this repo"             | `explore`          |
| "What does this module do"              | `explore`          |
| "Review my PR / check this code"        | `code-review`      |
| "Is there anything wrong here"          | `code-review`      |
| "I'm getting this error"                | `debugger`         |
| "This test is failing"                  | `debugger`         |
| "What should I test"                    | `test-engineer`    |
| "Help me write tests for X"             | `test-engineer`    |
| "Clean this up / simplify"              | `code-simplifier`  |
| "This is too hard to read/maintain"     | `code-simplifier`  |
| "Is this secure / audit this"           | `security-review`  |
| "Check auth / payments / uploads"       | `security-review`  |

Multiple modes may apply — for example, reviewing code (`code-review`) then
auditing it (`security-review`), or debugging a failure (`debugger`) then
designing a regression test (`test-engineer`).
