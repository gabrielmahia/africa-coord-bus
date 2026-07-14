# Porting the coordination bus to a new country

*Written after porting Kenya → Tanzania (Gap Register G8). A standard with one
implementation is a prototype; this guide exists because the second one taught us
what the first could not.*

## What you actually have to do

1. **Copy the portable cascades.** Roughly two-thirds transfer with threshold
   changes only. See `PORTABLE_PATTERNS` in `tanzania.py` for the audited list:
   drought→insurance, drought→crop advisory, outbreak→water quality,
   price_spike→food security, flood→disease risk.

2. **Change the staple basket, not the cascade.** Kenya's advisories lean maize;
   Tanzania's lean cassava/sorghum. The *shape* of drought→advisory is identical.
   If you find yourself redesigning the cascade, you are probably modelling a
   genuinely new hazard — see step 4.

3. **Do NOT hardcode the subnational unit.** This is the single biggest lesson.
   Kenya cascades to *counties*; Tanzania cascades to *regions (mikoa)* and
   *districts (wilaya)*. Target the **role** — "subnational authority" — never the
   Kenyan noun. A table that says `county` is not a standard, it is a Kenya table.

4. **Expect one cascade class nobody needed before.** Tanzania's pastoralist
   livestock economy required destocking and migration-as-health-signal cascades
   that Kenya's table has no trigger for. Country #3 should budget for discovering
   at least one of its own. If you find none, you probably have not looked hard at
   what your country's economy actually runs on.

5. **Then look across the border.** The cascades a *single* country cannot express
   are the highest-value thing a second implementation unlocks. Drought across the
   Kenya–Tanzania rangeland is one event: herds migrate ahead of it, carrying
   grazing pressure and disease into districts that had no drought of their own.
   See `CROSS_BORDER_TABLE`.

## Known defect the port exposed (unfixed, deliberately)

`CoordinationEvent.location` is typed **`KenyaLocation`** (fields: `county`,
`sub_county`). The bus encodes Kenya *in the type system*, not merely as a default.

This was invisible for the entire life of the single-country implementation. It is
exactly the class of lock-in that only a second country reveals.

**It is not fixed in this release, on purpose.** Renaming the type would break every
existing consumer, and a port must not regress a working system. The correct fix is
a backwards-compatible `SubnationalLocation` with `KenyaLocation` retained as an
alias. Until then, Tanzania rules carry location in `event.data`.

*Tracked in the Gap Register. Proposed, not imposed.*

## Checklist for country #3

- [ ] Audit `PORTABLE_PATTERNS` — take what transfers
- [ ] Rewrite thresholds for local hazard seasonality (unimodal vs bimodal rainfall, etc.)
- [ ] Replace the staple basket
- [ ] Identify your subnational unit — and target the role, not the noun
- [ ] Find the cascade class your economy needs that neither predecessor had
- [ ] Model the border you share with an existing implementation
- [ ] Contribute the port back, and update this guide with what *you* learned

The guide gets better every time someone uses it. That is the point.
