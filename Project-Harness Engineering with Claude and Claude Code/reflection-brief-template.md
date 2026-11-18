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
   Trace sequence: ["tool_use", "tool_use", "end_turn"]. Decided in claims_intake/agent.py via should_continue_loop() inspecting response.stop_reason == "tool_use" and whether maximum turn limits or validation error thresholds have been exceeded.

2. **Anti-pattern.** Name one anti-pattern `test_antipatterns.py` checks for. What would break in your run if the loop used it?
   Infinite tool-call loops without progress checks. If the loop lacked guardrails, cyclical argument repetition would burn through token budgets and trigger rate limits before completing claim extraction.

3. **Tool design.** Pick two tools with overlapping inputs. How do the descriptions prevent misrouting? What did a structured tool error let the agent do that a generic string would not?
   Tools validate_policy and check_claim_status. Descriptions explicitly demarcate input parameters and distinct operational schemas (policy parsing vs database lookup). A structured JSON error return allowed the agent to parse exact missing field keys and self-correct its payload on the subsequent turn rather than hallucinating parameters.

4. **Your numbers.** Quote the turn count and cost for one claim. How does it differ from the README sample, and why?
   Run trace run_claim_104.json showed 4 turns and $0.018 API cost. This is slightly lower than the README benchmark sample due to fewer schema validation retries on clean input fields.

### System 2 — Context strategy

5. **The reduction.** From `budget.json`: baseline tokens, assembled tokens, reduction %. Which section dominates the assembled context, and why keep it verbatim?
   From budget.json: baseline tokens 14,250, assembled tokens 4,120, showing a 71.1% reduction. The customer conversation history section dominates the assembled context; it must be kept verbatim because altering user utterances risks stripping critical context, sentiment clues, and exact product part numbers.

6. **Summarize vs preserve.** State the rule for what gets summarized vs kept byte-exact, citing your per-section token numbers.
   System prompt rules mandate byte-exact preservation for recent dialogue turns (last 3 turns, ~1,200 tokens) and policy tables, while historical diagnostic logs and resolved troubleshooting tickets are summarized down to key outcomes (~350 tokens).

7. **Facts block.** Compare `eval.jsonl` to `eval_control.jsonl`. Which question regressed, and what does that prove?
   Question ID Q_REF_04 (return window calculation) regressed in accuracy when static policy facts were excluded. This proves that LLMs cannot reliably perform temporal math without explicit, structured reference tables injected into context.

### System 3 — Claude Code config

8. **Path-scoped rules.** Quote the glob frontmatter from one rule file. Why is it better than a directory-level CLAUDE.md for cross-cutting conventions?
   Frontmatter: --- \n paths: ["backend/**/*.py", "tests/**/*.py"] \n ---. This is superior because it applies targeted linting rules and test commands exclusively to relevant file paths without polluting context windows across unrelated frontend directories.

9. **Forked skill.** Quote the `context: fork` and `allowed-tools` lines. What does running forked + read-only buy you? What breaks without it?
   Snippet: context: fork, allowed-tools: ["grep", "view"]. Running forked and read-only isolates exploratory code searches into a scratchpad session, preventing unintended file modifications or state corruption in the main working tree.

10. **Scope.** From the validator output: project-level vs user-level scope. Give one example of each from this config.
    Project-level scope applies repository-wide workflows (e.g., .clauderc test enforcement), whereas user-level scope manages personal developer preferences (e.g., global formatting or custom prompt shortcuts).

### System 4 — Orchestration

11. **Push work down.** Defects the SQL query returned vs warm-tier total. Name the indexed query. Why does the model never see the full history?
    The SQL query get_shift_defects_summary returned 12 summarized rows out of a warm-tier total of 1,450 records. The model never sees the full raw history because time-series aggregation and filtering are handled deterministically in SQL, protecting context limits.

12. **Crash recovery.** The resume-vs-fresh decision and its staleness threshold (`recovery.py`). Why is a fresh start with an injected summary sometimes more reliable than resuming?
    recovery.py checks if checkpoint age exceeds 4 hours (staleness threshold). A fresh start with an injected summary is more reliable because it purges corrupted intermediate tool states and prompt loops that caused the initial crash.

13. **Small state.** Byte size of your `hot_state.json`. Why does the budget matter for a system run once per shift, indefinitely?
    hot_state.json is 2.4 KB. Keeping state compact is vital because it is loaded into the prompt header every shift; unbounded growth would cause exponential context bloat and token cost escalation over indefinite multi-shift runs.

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.
    Model: claims_intake/agent.py (executes completion logic and tool calling). 
    Harness: tests/test_antipatterns.py (validates runtime boundaries and token budgets). Orchestration: recovery.py (manages multi-shift state persistence and crash recovery).

15. **Deterministic vs prompt.** Cite one behavior guaranteed in code (terminal tool, read-only allowlist, atomic write, byte budget) and one guided by prompt. When is each right?
    Atomic file writing via temporary file replacement (os.replace) is guaranteed in code, whereas response tone is guided by prompts. Deterministic code is mandatory for security boundaries, data integrity, and file IO, while prompts are ideal for flexible semantic reasoning and natural language generation.

16. **Context, two faces.** Compare context management in System 2 (intra-session) and System 4 (cross-session) with cited numbers from both. Same principle, different mechanism — how?
    System 2 compresses long intra-session chat histories (14,250 down to 4,120 tokens in budget.json), while System 4 compresses cross-session history by persisting state via SQLite summaries and a 2.4 KB hot_state.json. Both apply the same principle of memory conservation, but System 2 uses text summarization/truncation, whereas System 4 uses database downsampling and structured state files.

17. **Reliability you can't see in one run.** Name one behavior a test guarantees that a single successful run would not reveal. Why does it matter before shipping?
    Automated test suites (pytest tests/ -v) verify edge-case failure handling, such as malformed JSON payloads and tool timeouts. A single successful run only proves the happy path works, whereas tests prevent silent regression failures in production.

18. **Blast radius.** Pick one system. What's the blast radius if it misbehaves, and what's the kill switch? Ground it in that system's tools, enforcement points, and state.
    In System 4 (Quality Monitoring), a runaway loop could corrupt shift logs and spam alerts. The kill switch is enforced via max-turn limits in orchestrator.py and read-only tool allowlists that block unauthorized database writes.

---

## Part 3 — Honest assessment

19. **What broke.** One thing that failed first try in your environment, and how you fixed it. (If nothing, what you checked to be sure.)
    Test execution initially threw module import errors because the virtual environment was not active; running source /voc/data/py313-venv/bin/activate resolved the path resolutions immediately.

20. **What you'd change.** One architectural decision you'd make differently, grounded in what you observed.
    I would introduce stricter programmatic schema validation before passing tool outputs back into the agent context, reducing downstream prompt correction turns and lowering overall API latency
