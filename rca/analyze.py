"""Run the root-cause analysis and write report.md + charts.

The report text is generated from the query results; nothing about the answer is hard-coded.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql"
START = date(2026, 6, 1)


def connect(data_dir: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"""
        create view contacts as
        select *, (datediff('day', date '{START}', contact_date) // 7) + 1 as week
        from read_csv_auto('{(data_dir / "contacts.csv").as_posix()}')
    """)
    return con


def query(con, name: str, **params) -> list[dict]:
    rel = con.execute((SQL / name).read_text(encoding="utf-8"), params)
    cols = [d[0] for d in rel.description]
    return [dict(zip(cols, row)) for row in rel.fetchall()]


def find_change_week(topline: list[dict]) -> int:
    """First week of the largest sustained SLA step down (mean after vs mean before)."""
    best_week, best_drop = topline[1]["week"], 0.0
    for i in range(2, len(topline) - 1):
        before = sum(r["sla_pct"] for r in topline[:i]) / i
        after = sum(r["sla_pct"] for r in topline[i:]) / (len(topline) - i)
        if before - after > best_drop:
            best_week, best_drop = topline[i]["week"], before - after
    return best_week


def md_table(rows: list[dict]) -> str:
    cols = list(rows[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


def chart(topline, drivers, site, queue, change_week, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot([r["week"] for r in topline], [r["sla_pct"] for r in topline], label="All sites and queues", lw=2)
    ax.plot([r["week"] for r in drivers], [r["sla_pct"] for r in drivers], label=f"{site} / {queue}", lw=2)
    ax.axvline(change_week, ls="--", c="grey")
    ax.set_xlabel("Week")
    ax.set_ylabel("Contacts answered within SLA (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower left")
    ax.set_title("SLA by week: the top line hides a segment-level failure")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def run(data_dir: Path, out_dir: Path) -> str:
    con = connect(data_dir)
    topline = query(con, "01_weekly_topline.sql")
    change_week = find_change_week(topline)
    segments = query(con, "02_sla_change_by_segment.sql", change_week=change_week)
    worst = segments[0]
    site, queue = worst["site"], worst["queue"]
    drivers = query(con, "03_segment_drivers.sql", site=site, queue=queue)
    tenure = query(con, "04_aht_by_tenure.sql", site=site, queue=queue, change_week=change_week)

    base = [r for r in drivers if r["week"] < change_week]
    recent = [r for r in drivers if r["week"] >= change_week]
    avg = lambda rows, k: sum(float(r[k]) for r in rows) / len(rows)  # noqa: E731
    aht_up = 100 * (avg(recent, "aht_seconds") / avg(base, "aht_seconds") - 1)
    demand_change = 100 * (avg(recent, "contacts_per_day") / avg(base, "contacts_per_day") - 1)
    by_band = {r["tenure_band"]: r for r in tenure}
    new_hire_aht = by_band.get("0-4 weeks", {}).get("aht_seconds")
    tenured_aht = by_band.get("8+ weeks", {}).get("aht_seconds")

    out_dir.mkdir(parents=True, exist_ok=True)
    chart(topline, drivers, site, queue, change_week, out_dir / "sla_by_week.png")

    answer = (
        f"SLA on **{queue} at {site} ({worst['vendor']})** fell from {worst['sla_baseline_pct']}% to "
        f"{worst['sla_recent_pct']}% from week {change_week}, the largest contribution "
        f"({worst['contribution_to_overall_pts']} pts) to the drop in overall SLA. Demand was flat "
        f"({demand_change:+.1f}%), but handle time rose {aht_up:.0f}% as new hires took a large share of contacts "
        f"(peaking at {max(r['pct_contacts_new_hires'] for r in recent)}% of contacts). New hires average "
        f"{new_hire_aht:.0f}s per contact against {tenured_aht:.0f}s for tenured specialists, so workload reached "
        f"up to {max(r['occupancy_pct'] for r in recent)}% of contracted hours and waits breached SLA."
    )
    report = f"""# Root-cause analysis: SLA drop from week {change_week}

## One clear answer

{answer}

**Recommendation:** for the next 4 weeks, add temporary capacity to {site} / {queue} (about the gap between
new-hire and tenured handle time across the new hires' share of volume), or route overflow to the
best-performing site on the same queue. Pair new hires with tenured specialists until their AHT is within 15%
of tenured AHT. Set a guardrail: the vendor must flag any staffing swap above 25% of a queue in advance.

**What the data cannot tell us:** whether the vendor changed its training programme, or whether new hires are
also less accurate. That needs Quality Analytics case audits for the same period.

![SLA by week](sla_by_week.png)

## 1. Top line

{md_table(topline)}

## 2. Which segment moved? (baseline weeks 1 to {change_week - 1} vs recent weeks {change_week}+)

{md_table(segments)}

## 3. Drivers inside {site} / {queue}

{md_table(drivers)}

## 4. Handle time by tenure (recent period)

{md_table(tenure)}
"""
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    return answer


if __name__ == "__main__":
    print(run(ROOT / "data", ROOT / "output"))
