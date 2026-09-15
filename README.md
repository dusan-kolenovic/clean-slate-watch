# Clean Slate Watch

More states now pass laws that automatically seal or expunge criminal records. Every one of them permanently shrinks the pool of records a background screening company can search. This project tracks that.

Two things live here.

## The news feed

A live page that lists the most recent developments in clean slate legislation, most recent first. It updates itself while it is open. Everyone at the company sees the same feed and the same read marks.

Each item carries the facts, not a headline. You should not need to open the link.

## The feasibility study

Phase 1. It answers one question: can we track this reliably, and are the sources good enough to trust.

The answer is yes. The study shows the evidence, grades every source, and names the three problems that will break the system if we ignore them.

## What we proved

We pulled all 3,646 bills from Virginia's 2026 session with no API key and no scraping. We found SB230, enacted as Chapter 1127, which resets Virginia's record sealing dates.

We also found two problems worth keeping in mind.

1. Keyword matching fails in both directions. A first pass ranked a Department of Motor Vehicles bill above everything else and missed the only enacted law in the set.
2. Virginia's own summary file flags zero of 3,510 bills as approved for the 2025 session. Two record sealing laws passed that session. Read the action history instead.

## Sources

No account and no API key is needed for any of these.

| Source | Refresh | What it gives us |
|---|---|---|
| Virginia LIS bulk CSV | hourly | Every bill, full action history, chapter numbers |
| Open States Postgres dump | monthly | All 50 states, 10.2 GB, public domain |
| Collateral Consequences Resource Center RSS | irregular | Expert legal analysis of what a bill means |
| Google News RSS | minutes | Implementation news that never reaches a bill feed |

LegiScan covers all 50 states and refreshes daily, but it needs an account. We do not need it yet.

## Files

| File | What it is |
|---|---|
| `index.html` | The feasibility study |
| `board.html` | The news feed |
| `va_screen.py` | Screens a Virginia session for record sealing bills |
| `test_legiscan.py` | Validates the LegiScan API, if we ever add it |

## Run the Virginia screen

```
curl -o va_20261.csv https://lis.blob.core.windows.net/lisfiles/20261/BILLS.CSV
curl -o va_sum_2026.csv https://lis.blob.core.windows.net/lisfiles/20261/Summaries.csv
python3 va_screen.py
```

## Still to build

Phase 2 is the pipeline that collects, classifies and writes new items into the feed. Four days of work for four states. Right now the items are written by hand.
