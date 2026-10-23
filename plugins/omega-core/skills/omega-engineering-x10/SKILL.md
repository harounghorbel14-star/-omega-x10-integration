---
name: omega-engineering-x10
description: Master router for the OMEGA-ENGINEERING X10 skill ecosystem (agent-browser, Grill Me and Matt Pocock skills, Replica, Everything Claude Code, find-skills, claude-mem, VibeSec, UI UX Pro Max, Superpowers, Graphify). Use at the start of any non-trivial engineering task to pick the right specialist skill, when the user asks "which skill should I use", "what can you do for X", or when a task spans several phases (requirements, planning, implementation, testing, security, design, review, release). Also use to diagnose why a specialist skill cannot run (missing CLI, worker, or plugin).
---

# OMEGA-ENGINEERING X10 router

This skill does not do the work itself. It picks the specialist skills that do, checks that
they can actually run, and keeps the engineering workflow honest.

The registry and the router script ship next to this file:

- `../../registry/skills.json`: every loaded skill from the ten sources (invocation, plugin,
  description, topics, detected dependencies).
- `../../registry/routing-rules.json`: curated routes with a primary skill, alternatives,
  requirements, fallbacks and precedence rules.
- `../../registry/capabilities.json`: topics, ECC agents and slash commands.
- `../../scripts/omega.py`: `route`, `doctor`, `list`, `show`, `check-routes` (Python 3 standard library only).

Paths are relative to this skill's base directory.

## Procedure

1. **Route.** Run `python3 <base>/../../scripts/omega.py route "<the user's task in one line>"`.
   It prints matching curated routes and the best keyword matches over all registered skills.
   For a quick decision you may read `routing-rules.json` directly instead.
2. **Check it can run.** If the chosen skill lists a requirement (agent-browser CLI, graphify CLI,
   claude-mem worker, npx), run `python3 <base>/../../scripts/omega.py doctor`. If something is
   missing, tell the user exactly what is missing and the fix command it prints, then use the
   route's `fallback`. Never say a browser action, graph build, memory search or install happened
   unless its command output shows it did.
3. **Check it is installed.** Each plugin is installed separately. If the routed skill's plugin is
   not enabled in this session, say which plugin to install
   (`/plugin install <plugin>@omega-engineering-x10`, or for claude-mem its upstream marketplace),
   and offer the fallback meanwhile.
4. **Invoke.** Load the specialist skill (Skill tool with the invocation name, e.g.
   `superpowers:systematic-debugging`) and follow it. For agent-browser's specialised content run
   `agent-browser skills get <name>` as its stub instructs.
5. **Combine without conflict.** Apply `precedence` from `routing-rules.json`: user request wins,
   then project instructions; one owner per phase (do not run two TDD workflows at once);
   security guidance is additive; verification before claiming completion is mandatory.

## Default engineering workflow

For real coding tasks follow `engineering_workflow` in `routing-rules.json`:
understand the repo, inspect constraints, clarify only material unknowns, plan complex work,
pick specialists, implement, add meaningful tests, run validation (separate regressions from
baseline failures), debug failures, review security/accessibility/performance/design,
inspect the final diff, report only verified results.

Do not stop at a plan when implementation was requested. Do not edit tests just to make them
pass. A skipped test is not a passing test.

## Quick map (see routing-rules.json for alternatives)

| Task | Primary | Notable alternatives |
|---|---|---|
| Unclear requirements | `mattpocock-skills:grill-me` | `superpowers:brainstorming`, `mattpocock-skills:grill-with-docs`, `ecc:council` |
| Find a skill | this router, then `find-skills:find-skills` | `ecc:skill-scout`, `mattpocock-skills:ask-matt` |
| Browser / web app interaction | `agent-browser:agent-browser` | `ecc:browser-qa`, `ecc:e2e-testing` |
| Session memory | `claude-mem:mem-search` | `mattpocock-skills:handoff`, `ecc:continuous-learning-v2` |
| Plan multi-step work | `superpowers:writing-plans` | `mattpocock-skills:to-spec`, `claude-mem:make-plan`, `ecc:blueprint` |
| Implement | `superpowers:executing-plans` | `superpowers:subagent-driven-development`, `mattpocock-skills:implement` |
| Tests / TDD | `superpowers:test-driven-development` | `mattpocock-skills:tdd`, `ecc:tdd-workflow`, `ecc:<lang>-testing` |
| Debugging | `superpowers:systematic-debugging` | `mattpocock-skills:diagnosing-bugs` |
| Code review | `superpowers:requesting-code-review` | `mattpocock-skills:code-review`, ECC reviewer agents |
| Security | `vibesec:vibesec` | `ecc:security-review`, `ecc:security-scan`, stack-specific `ecc:*-security` |
| UI / UX | `ui-ux-pro-max:ui-ux-pro-max` | `ui-ux-pro-max:design-system`, `ecc:frontend-design-direction`, `/design-review` |
| Repository architecture | `graphify:graphify` | `mattpocock-skills:improve-codebase-architecture`, `claude-mem:smart-explore` |
| Clone an app (clean-room) | `replica-skill:replica-recon` then the Replica pipeline | |
| Git / branches | `superpowers:using-git-worktrees` | `superpowers:finishing-a-development-branch`, `mattpocock-skills:pr` |
| Parallel agents | `superpowers:dispatching-parallel-agents` | `ecc:team-agent-orchestration` |
| Write a skill | `superpowers:writing-skills` | `mattpocock-skills:writing-for-agents` |
| Stack or domain specifics | `omega.py route "<stack> <task>"` | ~300 ECC language, framework and domain skills |

## Safety

- Do not install third-party skills, run network installers, or enable memory cloud sync without
  asking the user first and showing the source.
- claude-mem stores observations locally; `claude-mem:cloud-sync` and `claude-mem-cowork` send
  data to cmem.ai and are opt-in only. Never put secrets into memory.
- No push, force-push or protected-branch merge without explicit authorization.
