# Reflection Brief — Harness Engineering Capstone

**Name: Ranjana Joseph **

**Date: 18/11/2026 **

Replace each `→` with your answer. **Every answer cites at least one artifact from your own runs** — a run ID, file path, token count, claim outcome, or test count. Uncited answers do not pass. 3–6 sentences each unless noted. Paste short artifact snippets where they help.

**Environment**

- Model(s):claude-3-5-sonnet-20241022

- OS / Python:Linux / Python 3.13.x (/voc/data/py313-venv)

- Approx. API spend: ~$0.15–$0.40

---

## Part 1 — Per-system

### System 1 — Agentic loop

1. **Loop control.** Quote the `stop_reason` sequence from one trace. Name the file and function that decides continue-vs-stop, and how.

   Trace sequence: `["tool_use", "end_turn"]` from `runs/20261119_072951/traces/claim_03_water_damage.jsonl`.

The first model response requested the `lookup_policy` tool using policy ID `POL-1004`. The second response returned `end_turn`, completing the claim-processing loop. The continue-versus-stop logic is implemented in `claims_intake/loop.py`, inside the `run` function. The loop continues when `response.stop_reason == "tool_use"` and returns the final result when `response.stop_reason == "end_turn"`. Unexpected stop reasons are handled separately.

2. **Anti-pattern.** Name one anti-pattern `test_antipatterns.py` checks for. What would break in your run if the loop used it?

   One anti-pattern checked by `tests/test_antipatterns.py` is an agent loop without proper progress and termination guardrails. Without these checks, the agent could repeatedly request the same tool with identical arguments instead of making progress. This could waste tokens and API calls without completing claim processing. The loop's budget checks and termination handling help prevent this situation.

3. **Tool design.** Pick two tools with overlapping inputs. How do the descriptions prevent misrouting? What did a structured tool error let the agent do that a generic string would not?

   The `lookup_policy` and `record_claim_fact` tools both receive structured JSON inputs, but their purposes are different. `lookup_policy` requires a `policy_id` to retrieve coverage information, while `record_claim_fact` requires a `field` and `value` to store facts extracted from the claimant's statements. Their descriptions clearly explain when each tool should be used and what information it requires. The structured tool error response includes `is_error`, `error_category`, `is_retryable`, and `message`, allowing the agent to distinguish retryable failures from permanent errors instead of treating every error as an ordinary string.

4. **Your numbers.** Quote the turn count and cost for one claim. How does it differ from the README sample, and why?

  In run `20261119_072951`, the system processed eight claim fixtures with an estimated total API cost of $0.1184. For example, `claim_03_water_damage` completed in 2 turns at an estimated cost of $0.0069, while `claim_04_neighbor_injury` required 5 turns and cost $0.0234. The number of turns varied depending on the claim and the processing required. These are estimated costs recorded in the run's `summary.md`, rather than manually measured billing amounts.

### System 2 — Context strategy

5. **The reduction.** From `budget.json`: baseline tokens, assembled tokens, reduction %. Which section dominates the assembled context, and why keep it verbatim?

   The latest context assembly run (`20261119-074254`) recorded a baseline of 38,708 tokens and an assembled context of 16,811 tokens, giving a **56.57% reduction**. The assembled context contains 204 tokens of case facts, 389 tokens of resolved refund information, 447 tokens of resolved subscription information, and 15,789 tokens of active conversation context. This shows that the active conversation remains the largest part of the assembled context.

6. **Summarize vs preserve.** State the rule for what gets summarized vs kept byte-exact, citing your per-section token numbers.

   In `retail_context/assemble.py`, the active issue is preserved byte-exact, while resolved issues such as refund and subscription are represented by compressed summaries. Case facts are retained in a structured block at the top of the assembled context. In run `20261119-074254`, the section sizes were 204 tokens for case facts, 389 for resolved refund, 447 for resolved subscription, and 15,789 for the active issue. Preserving the active issue verbatim avoids losing details from the ongoing conversation, while compressing resolved issues reduces unnecessary context.

7. **Facts block.** Compare `eval.jsonl` to `eval_control.jsonl`. Which question regressed, and what does that prove?

   Question Q6 (the structured status of the payment-method update issue) failed in the control run but passed with the assembled context. Without the active issue's structured case facts, the model incorrectly stated that no status token was recorded. With the assembled context, it correctly returned the exact status `in_progress`. This demonstrates why preserving the active issue and its structured facts is important for answer accuracy.
### System 3 — Claude Code config

8. **Path-scoped rules.** Quote the glob frontmatter from one rule file. Why is it better than a directory-level CLAUDE.md for cross-cutting conventions?

  In `01-compose-modular-claude-code-configuration/solution/.claude/rules/tests.md`, the frontmatter uses these path globs: `**/*.test.tsx` and `**/*.test.ts`. The React rule in `.claude/rules/react.md` uses `src/components/**/*` and `src/pages/**/*`. These path-scoped rules load only for matching files, so test conventions apply across the repository without adding test-specific instructions to every file or loading them for unrelated work. This keeps conventions focused while allowing different rules to apply to different parts of the monorepo.

9. **Forked skill.** Quote the `context: fork` and `allowed-tools` lines. What does running forked + read-only buy you? What breaks without it?

   In `03-author-forked-deploy-check-skill/solution/.claude/skills/deploy-check/SKILL.md`, the skill declares `context: fork` and an `allowed-tools` list containing `Read`, `Grep`, `Glob`, and restricted Git and GitHub commands. Running it in a fork keeps verbose file-discovery and Git output out of the main session, returning only a structured summary. The read-only allowlist prevents the skill from modifying files, pushing changes, or deploying. Without these restrictions, an exploratory deployment check could interfere with the working tree or perform unintended actions.

10. **Scope.** From the validator output: project-level vs user-level scope. Give one example of each from this config.

    The validator artifact `evidence/claude-config-validator.txt` contains `OK`, confirming that the Claude Code configuration passed validation. Project-level configuration is stored in the repository, such as `.claude/skills/deploy-check/SKILL.md`, so the team shares the same deployment checks. User-level configuration belongs in the individual developer's home configuration, such as `~/.claude/skills/`, and can provide personal variants without changing the team's project configuration.

### System 4 — Orchestration

11. **Push work down.** Defects the SQL query returned vs warm-tier total. Name the indexed query. Why does the model never see the full history?

    System 4 uses SQLite in `shift_monitor/warm.py`. The `defects_since` method runs `SELECT * FROM defects WHERE ts > ? ORDER BY ts DESC LIMIT ?`, so filtering, sorting and limiting happen in SQL rather than Python. The database creates `idx_defects_ts` on the timestamp column and `idx_defects_shift_ts` on shift and timestamp. This reduces the amount of historical data passed to the model. The test `test_defects_since_uses_index_and_does_not_load_full_table` verifies this behavior.

12. **Crash recovery.** The resume-vs-fresh decision and its staleness threshold (`recovery.py`). Why is a fresh start with an injected summary sometimes more reliable than resuming?

    System 4 uses `shift_monitor/recovery.py` and its `decide` function to choose whether to resume or start fresh. If the manifest has no steps or is already complete, it starts fresh. If the last recorded step is within 30 minutes, it resumes; otherwise, it starts fresh and can use the findings already captured in the manifest as a summary. This avoids resuming stale partial work. The threshold is defined by `STALE_RESUME_THRESHOLD_MINUTES = 30`.

13. **Small state.** Byte size of your `hot_state.json`. Why does the budget matter for a system run once per shift, indefinitely?

    The generated `data/hot_state.json` file is 965 bytes, which is below the 5,120-byte budget. It contains recent defect hashes, the current shift summary, active alerts, and threshold statuses. Keeping this state compact matters because it is carried forward between shifts. A fixed size budget prevents state growth from increasing context usage and processing costs over time.

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.

   The model layer is represented by the Claude client and the prompt/invocation logic that sends the task to Claude. The harness includes the stop-reason-driven loop in `claims_intake/loop.py`, which controls tool execution and termination. Orchestration is represented by System 4's `shift_monitor/pipeline.py`, which gathers SQL-filtered defects, builds the prompt, calls Claude once, updates the hot state and appends a scratchpad entry. These layers separate reasoning, execution control and workflow coordination.

15. **Deterministic vs prompt.** Cite one behavior guaranteed in code (terminal tool, read-only allowlist, atomic write, byte budget) and one guided by prompt. When is each right?

    System 4 uses deterministic code for SQL filtering, timestamp cutoffs, recovery decisions, state-size limits and atomic file writing. For example, `pipeline.py` trims the hot state to its byte budget and calls `write_atomic` to persist it. The prompt guides Claude's interpretation of defect patterns and the natural-language shift summary. I would keep data integrity, storage and safety boundaries in code, while using prompts for flexible analysis and explanation.

16. **Context, two faces.** Compare context management in System 2 (intra-session) and System 4 (cross-session) with cited numbers from both. Same principle, different mechanism — how?

    System 2 manages intra-session context by assembling and compressing conversation history. Its `budget.json` for run `20261119-074254` records a reduction from 38,708 to 16,811 tokens, or 56.57%. System 4 manages cross-session context through persisted state, including `evidence/hot_state.json`, which is 965 bytes and stays below the 5,120-byte budget. Both systems conserve context, but System 2 uses structured summaries and selective preservation, while System 4 carries compact state between shifts.

17. **Reliability you can't see in one run.** Name one behavior a test guarantees that a single successful run would not reveal. Why does it matter before shipping?

    The System 4 test suite contains 33 passing tests covering state persistence, SQL filtering, invocation behavior, crash recovery and forked scratchpads. For example, `test_hotstate_roundtrip_and_size_budget` checks state serialization and the size limit, while `test_recovery_decide_truth_table` checks recovery decisions. These tests verify both normal behavior and important edge cases, helping prevent regressions when the implementation changes.

18. **Blast radius.** Pick one system. What's the blast radius if it misbehaves, and what's the kill switch? Ground it in that system's tools, enforcement points, and state.

    System 4 limits execution by making one Claude call per shift in `shift_monitor/pipeline.py`, rather than allowing an unrestricted agent loop. It also limits SQL retrieval to 50 defects, trims the hot state to the configured byte budget, and writes updated state atomically. These controls reduce unnecessary context, prevent oversized state files and protect persisted data from incomplete writes.

---

## Part 3 — Honest assessment

19. **What broke.** One thing that failed first try in your environment, and how you fixed it. (If nothing, what you checked to be sure.)

    During development, I encountered Python environment and module execution issues while running the project tests. I checked the active Python interpreter and ensured that the project was running in the provided Python 3.13 virtual environment. I then reran the tests and verified the results using the saved evidence logs.

20. **What you'd change.** One architectural decision you'd make differently, grounded in what you observed.

    I would improve the system by adding stricter schema validation for model responses before updating persisted state. Although the current pipeline handles invalid or missing JSON by falling back to a short text summary and retaining existing alert/status values, stronger validation would help detect incomplete or unexpected fields earlier. This would make state updates more reliable and reduce the risk of incorrect information being carried into the next shift.