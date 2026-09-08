# Risk Register

*Every risk with a **named trigger for change** — not a vague mitigation. A panel asking about
risk is testing whether you know what would falsify your plan.*

---

| Risk | Threat | Mitigation | **Trigger for change** |
| --- | --- | --- | --- |
| **Historical build rot** ⚠ *biggest* | Subjects may not build within semester time | Frozen containers and versions; report yield and exclusions honestly | Fewer than 3 reproducing cases *(cleared)*; inadequate held-out subset at **Mid-1** |
| **Invisible resources** ⚠ *second* | Polluter unranked, or explanation false through a normalisation error | Bound families; expose coverage; fall back to order evidence; abstain | True-polluter recall below the gate, **or any false confident certificate** |
| **Diagnosis signal too weak** | POC returned zero overlap at one hop | Depth sweep · per-case cause classification · order-outcome priors as a second input | **Depth-3 still fails the ranking gate on ≥3 of 5 cases** |
| **Single-project evidence** | All four reproduced cases came from one library | Out-of-domain subject before defence; state the limitation if it fails | Second project reproduces **no** cases |
| **Nearest-work overlap** | Six research tools cover parts of the claim | All become baselines; defend certificate, budget, abstention | **No measurable delta remains** → rescope before scope freeze |
| **Multi-predecessor cases** | Pairwise scan cannot find them **by construction** | 1-minimal wording · multi-test candidates retained · fixture F3 | Deletion checks **contradict** the certificate |
| **Instrumentation perturbation** | Tool changes what it measures | Overhead measurement; non-perturbation check against unmodified Surefire | Overhead exceeds the frozen limit |
| **Core replacement via LLM** | Contribution migrates into a third-party model | Templated generator **mandatory and ablatable**; product ships fully offline | Templated arm cannot be built |
| **Unsafe patches** | A patch that **suppresses rather than repairs** | Allowlist · escalation tiers · suppression detector · adversarial test set | **Any** false-verified patch |
| **Scope inflation** | Feature count dilutes the core problem | Written tiers with gates; excluded list kept out of the promise | FYP-I lacks end-to-end certificate **or** measured baseline |
| **Three-person overload** | Integration cost rises faster than headcount | Interface contracts frozen early; CDR gated; **a third member is not 1.5× delivery** | FYP-I milestones slip |
| **Secret leakage** | Paths or credentials in logs | Redaction before logging or transmission; offline flag | **Any** secret found in an artefact |
| **Stakeholder ecosystem mismatch** *(added)* | All recorded stakeholders are non-Java | Java corpora carry the technical claim; seek one Java/Maven practitioner | No Java practitioner secured **before defence** → state the limitation explicitly in the proposal |

---

## The two to name if asked "biggest risk" (Q94, Q95)

### 1. Historical build rot

> It is the risk that **gates everything downstream**, because without reproduced cases there is
> no benchmark, no baseline and no evaluation.

Evidence it is real, not theoretical: Tufano et al. found broken snapshots in **96%** of 100
Apache Maven projects, only **38%** of change history compilable. Rahman et al. lost **249 → 155**
on independent re-execution. **Our own POC reproduced 4 of 8.**

### 2. Invisible resources

> **Our POC is direct evidence that this risk is live rather than theoretical.**

Zero overlap at one hop was exactly this failure mode — the state moved through a path we were
not following.

---

## Fallback ladder — pre-registered

| If | Then |
| --- | --- |
| Resource recall stays weak at every affordable depth | **Order-outcome evidence carries the ranking**; resource events used only to certify explanations; **the contribution claim changes accordingly** |
| Adaptive policy does not beat the baselines | Reframe as a rigorous evidence-certified product and benchmark integration — **only if stakeholder and evaluation value remain substantial**. If not, **rescope before the scope freeze** |
| Clean sandboxing cannot be defended at evaluation | Limit the product to **explicitly trusted local projects** and state the boundary |
| Instrumentation overhead exceeds the frozen limit | Fall back to a **lighter collection mode** |
| Public projects will not build | Verified RankF subset with published yield → reduce case count **and report it** → never substitute synthetic-only results silently |
| Behind at Final-1 | Cut order: **CDR → filesystem evidence → adaptive policy**. Core end-to-end path is last |

> **Reporting a negative policy result honestly, with paired confidence intervals, is a
> legitimate evaluation outcome. Quietly changing the metric after seeing the result is not** —
> which is why the thresholds are frozen before the held-out run.

---

## Ethics, legal and DEI

### Legal
All subject projects open source, licences recorded in the manifest (**MIT** for
json-iterator/java, **Apache-2.0** for alibaba/fastjson). Source fetched by script at pinned
commits and **never redistributed** — our evidence bundle contains manifests, logs, results and
our own code, **not third-party source**. IDoFT is publicly available research data containing
no personal information.

### Ethics
No human subjects beyond voluntary usability sessions with **informed consent** and no personal
data collection. Untrusted third-party test code executes only in rootless containers with
networking disabled, capabilities dropped and resource limits enforced. Secrets, credentials and
user paths redacted before any logging or export.

> **The tool never claims definitive causality** — it states evidence, provenance and
> limitations, and **abstains when the evidence is insufficient**.

Any LLM component operates only on **redacted, certificate-directed code slices**, with a
configuration flag disabling all external calls for users who cannot send code off-premises.

**Three ethical issues, named (Q99):** executing third-party code · handling source and test
output that may contain proprietary information or credentials · **responsible claim-making** —
issuing a confident diagnosis that is wrong causes a developer to modify working code, which is
why abstention and the false-confidence metric exist.

### DEI
Self-hosted and **free to run** — no cloud subscription, no GPU, no paid API required for the
committed product, so it is usable by **under-resourced teams and institutions**. A
plain-language explanation mode makes the output usable by junior developers and non-native
English speakers rather than only by test-infrastructure specialists. By reducing reliance on
scarce senior engineering expertise, it **widens who is able to diagnose these failures**.
