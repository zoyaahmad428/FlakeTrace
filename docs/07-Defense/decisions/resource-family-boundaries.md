# Decision: three committed resource families, everything else opaque

**Status:** `COMMITTED` · **Owner:** Member 1

---

## The decision

**Committed (fully diagnosed):**
| Family | Identity normalisation |
| --- | --- |
| JVM static fields | declaring class + field name + descriptor, **resolved through the class loader** so the same field seen from two loaders is not counted as two resources |
| Java system properties | key |
| Filesystem paths | canonicalised — symlinks resolved, relative paths resolved against the recorded working directory, temp directories normalised so a per-run temp path does not appear as a distinct resource every execution |

**Not diagnosed:** databases · network · caches · services · threads · timing · reflection.

## Why these three

They are precisely the families for which the literature demonstrates **tractable,
inspectable evidence extraction**:

- **Zhang et al.** identify static fields and the file system among root causes of dependence
- **PolDet** operationalises this — finds tests modifying a heap location shared across tests
  or a file on disk, and reports an **access path through the heap** or the **name of the
  modified file** as evidence
- **Rahman et al.** enumerate static variables and the file system among the global state
  through which OD failures occur
- **Luo et al.** found **47%** of the order-dependency cases they inspected were caused by
  dependence on **external resources** rather than in-memory state alone — which is precisely
  why filesystem paths are committed as a first-class family rather than deferred

## Why the exclusions

> Supporting databases and networks honestly means writing a **resource adapter per
> technology**, and each carries its own identity-normalisation problem — two JDBC connections
> to the same logical table, two file paths through a symlink.
>
> We would rather support **three families completely and expose the rest as declared coverage
> gaps** than support seven badly and produce explanations we cannot audit.

## The system does not go silent on excluded families

An unsupported resource produces an **opaque event**, which:
- contributes to the **abstention decision** (reason: `unsupported resource`)
- appears in the **coverage report**

> That is why abstention is a committed feature rather than an excuse.

Frozen definition wording: reflection, filesystem, system properties, network and database
state are *"out of scope and recorded as unsupported, **never as zero-overlap**."* — the
distinction matters, because recording an unsupported family as zero would manufacture a
false negative.

## The identity-normalisation risk

> Identity normalisation is where this gets hard, and **getting it wrong produces false edges
> that look like explanations.**

Controls: every reported overlap names the **exact field and bytecode locations**, and false
or unknown edges are **retained in the graph rather than dropped**.

## Known tension with our stakeholder evidence

Our three interviewed practitioners describe polluted state that is largely **database rows on
shared staging instances** — which sits in the excluded list. This is part of the wider
ecosystem gap recorded in [[07-Defense/weak-points]] §1 and must not be glossed over.

The defence is that the *problem shape* and *design commitments* transfer; the *resource
abstraction* is JVM-specific by design, and a different ecosystem needs a different
abstraction, not a configuration flag.

## Panel answer (Q11)

> Because supporting them honestly means writing a resource adapter per technology, and each
> adapter carries its own identity-normalisation problem — two JDBC connections to the same
> logical table, two file paths through a symlink. We would rather support three families
> completely and expose the rest as declared coverage gaps than support seven families badly
> and produce explanations we cannot audit.
>
> The system does not go silent on them. An unsupported resource produces an opaque event,
> which contributes to the abstention decision and appears in the coverage report. That is why
> abstention is a committed feature rather than an excuse.
