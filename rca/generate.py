"""Simulate 12 weeks of contacts for a multi-site, multi-vendor trust & safety operation.

A root cause is planted in week 8: the Manila site (Vendor B) onboards a wave of new specialists onto the
Account Takeover queue. New hires handle contacts more slowly, occupancy rises and SLA falls. The analysis
in sql/ has to find this from the data alone.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SITES = {"Lisbon": "In-house", "Dublin": "In-house", "Manila": "Vendor B", "Bogota": "Vendor A"}
QUEUES = {"Account Takeover": 540, "Payment Fraud": 600, "Listing Safety": 420}  # base AHT in seconds
SLA_SECONDS = 3600
START = date(2026, 6, 1)
WEEKS = 12
INCIDENT_WEEK = 8


def generate(out_dir: str | Path, seed: int = 11) -> Path:
    rng = random.Random(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    specialists = []
    sid = 0
    for site, vendor in SITES.items():
        for queue in QUEUES:
            for _ in range(8):
                sid += 1
                specialists.append({"specialist_id": sid, "site": site, "vendor": vendor, "queue": queue,
                                    "start_date": (START - timedelta(weeks=rng.randint(10, 80))).isoformat()})
    # The planted change: 10 new hires join Manila / Account Takeover in week 8 and 4 tenured specialists leave.
    incident_start = START + timedelta(weeks=INCIDENT_WEEK - 1)
    leavers = {s["specialist_id"] for s in specialists if s["site"] == "Manila" and s["queue"] == "Account Takeover"}
    leavers = set(sorted(leavers)[:4])
    for _ in range(10):
        sid += 1
        specialists.append({"specialist_id": sid, "site": "Manila", "vendor": "Vendor B", "queue": "Account Takeover",
                            "start_date": incident_start.isoformat()})
    for s in specialists:
        s["end_date"] = (incident_start - timedelta(days=1)).isoformat() if s["specialist_id"] in leavers else ""

    contacts = []
    cid = 0
    for day in range(WEEKS * 7):
        d = START + timedelta(days=day)
        for site in SITES:
            for queue, base_aht in QUEUES.items():
                team = [s for s in specialists if s["site"] == site and s["queue"] == queue
                        and date.fromisoformat(s["start_date"]) <= d
                        and (not s["end_date"] or date.fromisoformat(s["end_date"]) >= d)]
                volume = int(rng.gauss(55, 6))
                # Contracted hours are fixed per site and queue: replacing tenured staff with new hires
                # does not add capacity, it only changes how fast the same hours clear work.
                staffed_seconds = 38_000
                rows = []
                for _ in range(volume):
                    spec = rng.choice(team)
                    tenure_weeks = (d - date.fromisoformat(spec["start_date"])).days / 7
                    slowdown = 1.6 if tenure_weeks < 4 else (1.25 if tenure_weeks < 8 else 1.0)
                    aht = max(60, rng.gauss(base_aht * slowdown, base_aht * 0.15))
                    rows.append((spec, aht, tenure_weeks))
                occupancy = sum(r[1] for r in rows) / staffed_seconds
                for spec, aht, tenure_weeks in rows:
                    cid += 1
                    # Waiting time grows sharply once occupancy goes above ~85%.
                    mean_wait = 900 * math.exp(4 * max(0.0, occupancy - 0.85)) * (0.8 + 0.4 * rng.random())
                    wait = rng.expovariate(1 / mean_wait)
                    contacts.append({
                        "contact_id": cid, "contact_date": d.isoformat(), "site": site, "vendor": SITES[site],
                        "queue": queue, "specialist_id": spec["specialist_id"],
                        "tenure_weeks": round(tenure_weeks, 1), "handle_seconds": round(aht),
                        "wait_seconds": round(wait), "within_sla": int(wait <= SLA_SECONDS),
                    })

    for name, rows in [("specialists", specialists), ("contacts", contacts)]:
        with (out / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    return out


if __name__ == "__main__":
    print(generate("data"))
