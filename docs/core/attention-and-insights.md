# Attention cards and insights

A cross-module platform service (stories US-501 to US-503). Modules **publish candidate evidence** through their public contracts; the attention service ranks a small number of cards, each with a reason, supporting sources, freshness and an acknowledge/dismiss action.

Rules:
- Bounded: limited count per surface; ranked by explicit, documented priority.
- Explainable: every card cites its evidence records and data states.
- Deterministic outcomes first; an LLM may phrase explanations or extract proposals but never decides availability, conflicts or amounts.
- Sensitive classes (health, finance, children) produce cards only on surfaces and for audiences allowed by enablement; never on shared screens unless masked.
- Read-only: a card may suggest; it never acts.

Module-specific insight submodules (household/insights, finance/insights) own their domain analysis; the attention service only selects and presents.
