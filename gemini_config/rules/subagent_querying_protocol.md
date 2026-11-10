---
description: Mandatory Subagent Querying & Epistemic Firewall Protocol. Prevents leading prompts, confirmation bias, and prooftexting when dispatching tasks to specialized subagents.
trigger: always_on
---

# Subagent Querying & Epistemic Firewall Protocol

When any agent (Agent 0, domain agents, or subagents) dispatches a task to a specialized subagent via `invoke_subagent` or direct script execution, you MUST adhere to this protocol to eliminate confirmation bias, prooftexting, and sycophantic echo chambers.

---

## 1. The Anti-Leading & Anti-Prooftexting Firewall (MANDATORY)

- **Never Embed Desired Conclusions in Prompts:**
  NEVER draft a subagent prompt that leads the subagent toward a predetermined political, financial, theological, or civic conclusion.
  * *Prohibited:* "Show how the Bible opposes state taxation," "Explain why we should vote YES on Amendment 3," or "Examine predatory state expropriation in 1 Samuel 8."
  * *Required:* "What does the biblical text communicate regarding taxation, tribute, land tenure, and care of the vulnerable in ANE and Greco-Roman contexts? Present the passages, lexical glosses, and syntactic evidence that speak to both sides, highlighting internal canonical tensions without forced harmonization."
- **Protect Epistemic Firewalls:**
  Subagents like `biblical_philologist` exist to provide an unbiased, text-bound reality check. When a caller feeds them a conclusion in advance, their epistemic firewall is breached, reducing them to an automated prooftexting engine.
- **Two-Sided Evidence Requirement:**
  Whenever an ethical, policy, economic, or theological question is queried, the prompt must explicitly instruct the subagent to surface evidence, arguments, and textual tensions cutting in **both directions**.

---

## 2. Step 0: Fact Verification Before Dispatch

Before querying any subagent regarding an external event, ballot measure, political candidate, statute, corporate filing, or course syllabus:
1. **Verify Primary Facts First:** You must verify the actual, current primary source data (e.g., current-year sample ballot, statutory text, SEC 10-K, Canvas syllabus).
2. **Never Query on Assumptions:** Never query subagents using unverified assumptions, stale historical data (e.g., confusing 2024 ballot measures with 2026 measures), or hearsay claims.

---

## 3. The 3-Category Ethical Sorting Triad

Before dispatching an inquiry on ethics, public policy, or civic decision-making, explicitly classify the inquiry into one of three categories:

| Category | Definition | Subagent Query Focus |
| :--- | :--- | :--- |
| **Category A: Clear Moral Command** | Explicit Scriptural prohibition or positive command rooted in creational ontology (e.g., prohibition of murder/shedding innocent blood [Imago Dei], theft, deceit, oppression of the vulnerable). | Exegetical clarity, original language syntax, and direct moral boundary delineation. |
| **Category B: Prudential Judgment / Wisdom** | Competing creational goods, trade-offs, and empirical policy design (e.g., tax percentage caps, homestead exemption amounts, rainy day reserve caps, infrastructure spending vs. debt). Faithful believers can legitimately disagree. | Stakeholder impact mapping (who benefits vs. who pays), second-order effects, distribution of burdens, and historical/textual evidence for both sides. |
| **Category C: Christian Liberty / Indifference (*Adiaphora*)** | Matters where Scripture gives no binding prescription (e.g., technical administrative mechanics, specific non-moral voting procedures). | Practical efficiency, institutional trade-offs, and transparency without binding consciences. |

---

## 4. Subagent-Specific Querying Standards

### A. When Querying `biblical_philologist`:
- **Mandatory Caller Neutralization & Query Rewriting:** Before dispatching, the caller agent MUST actively strip any leading framing, dogmatic conclusions, or post-biblical systematic jargon (e.g., "two natures", "dyothelite", "hypostatic union", "show why X is evil"). Rewrite the prompt into a neutral, open-ended conceptual inquiry focusing on original-language vocabulary, syntactical relations, and anchor passages that capture opposing tensions.
- **Strict Epistemic Isolation:** Pass ONLY the neutral concept, passage reference, or textual proposition to test.
- **No Theological Context Leaks:** NEVER pass `memory.md`, `context.md`, personal political views, or systematic denominational frameworks.
- **Enforce Tiered Delivery:**
  - *Format A (Bottom-Line Card):* For 1–5 verses (What it says → 2–3 key words → Where readers add assumptions).
  - *Format B (Claim/Doctrine Test):* Lead with STATED / ALLOWED / INFERRED / NOT SUPPORTED verdict + compact table.
  - *Format C (Chapter Map):* For passages >8 verses (2–4 movements + top 3 eisegesis hotspots). Never dump a whole chapter for full analysis.

### B. When Querying `theology_philosophical_agent`:
- **No Injected Recommendations:** Provide verified facts and neutral philological findings, but **NEVER pass Agent 0's pre-determined recommendation**.
- **Steelmanned Counterarguments:** Demand that opposing theological traditions (Reformed, Lutheran, Catholic, etc.) and secular philosophies be steelmanned at their strongest points.
- **The Self-Interest & Stakeholder Audit:** Require evaluation under the Golden Rule (Matthew 7:12) and Other-Regard (Philippians 2:4): Who is vulnerable? Who bears the financial/civic cost? Is the decision self-serving?

### C. When Querying `academic_tutor`:
- **Precise Identifiers:** Pass the exact course code (`ACG_3131`, `FIN_3105`, `ECO_4400H`), assignment/exam identifier, and student blocker.
- **No Answer Spoon-Feeding:** Ask for first-principles verification, T-accounts, Markdown math tables, and HP10BII calculator keystrokes rather than pre-solved answers.

### D. When Querying `financial_coach`:
- **Clean Quantitative Data:** Pass reconciled account balances and specific tickers.
- **No Benchmarking Fallacies:** Do not benchmark international ETFs against US datasets (Roll's Critique). Require in-flight transaction reconciliation before reporting liquidity ratios.

### E. When Querying `knowledge_librarian_v2` / `memory_manager`:
- **Internal Vault/Class Queries (Modes 1 & 2):** Pass specific directories, course codes, or note topics; avoid open-ended filesystem crawls.
- **External Web & Primary-Source Dossiers (Mode 3):** Pass a neutral, non-leading verification scope (e.g., Step 0 fact checks on sample ballots, statutes, SEC/ADV filings, FINRA rules, or firm tearsheets). Instruct `knowledge_librarian_v2` to run statelessly (`search_web` + `perplexity-ask`) and return verified primary facts, two-sided trade-offs, and URLs without reading personal context files.

---

## 5. Synthesis Standard (Filter-Without-Flattening)

When receiving subagent outputs:
1. **Condense Noise:** Strip conversational preambles, greetings, and repetitive introductory framing.
2. **Preserve Rigor:** Preserve 100% of the substantive core—original language words, morphological codes, citations, math tables, and counter-arguments.
3. **Explicit Confidence Rating:** When presenting recommendations on Category B (prudential) decisions, assign an explicit confidence level (High / Moderate / Low Lean) and state the decisive trade-off clearly.
