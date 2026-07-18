# Model-endpoint neutrality

Agents built on this bus must be able to change model suppliers without code
changes. This is a resilience requirement, not a convenience: access to any
single source — a closed US API, a Chinese open-weight host, a local GPU —
should be treated as revocable. Sovereignty is the ability to switch.

## The pattern (use existing tools; do not build a router)

Per doctrine (BAOBAB_DNA rule 3), we standardize on the OpenAI-compatible
`/chat/completions` convention and existing proxies rather than writing routing
code:

1. **Configuration, not code.** Agents read `KIPIMO_BASE_URL` / `KIPIMO_API_KEY`
   (or your own `*_BASE_URL` pair) from the environment. Swapping Claude → Kimi K3
   → a vLLM server on in-region hardware is an env change.
2. **One proxy when you need fan-out.** [LiteLLM](https://github.com/BerriAI/litellm)
   already speaks 100+ providers behind one OpenAI-compatible endpoint, with
   fallbacks and budgets. Run it as a sidecar; point `BASE_URL` at it.
3. **Offline-first still applies.** The bus queues events to JSONL regardless of
   which endpoint is up. Endpoint failure is a routing event, not a data loss event.
4. **Score before you switch.** Any candidate endpoint gets a kipimo run first
   (`pip install kipimo`; see kipimo docs/SCORECARD.md). Family matters: a
   `small-open` model that scores within a few points of a frontier API may be
   the right choice at 1/100th the cost — that is the leapfrog case, measured.

## Anticipating in-region inference

GPU capacity is arriving on the continent (multi-country build-outs announced
for 2026). When in-region OpenAI-compatible endpoints exist, agents following
this pattern adopt them with zero code changes — and inference locality becomes
a routing dimension the bus can carry in event metadata (see G10 in the Gap
Register for the location-typing prerequisite).
