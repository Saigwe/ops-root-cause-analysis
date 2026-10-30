# 3-minute walkthrough: Operations Root-Cause Analysis

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, `output/sla_by_week.png`, the four files in `sql/`, `rca/analyze.py`, `output/report.md`, GitHub Actions.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | When a frontline metric moves, leadership asks why, and the hard part is answering quickly and with evidence. This finds the cause of an SLA drop across sites, vendors and queues. |
| 0:20–0:40 | README intro | Twelve weeks of simulated contacts, about 50,000, for a multi-site, multi-vendor trust and safety operation, with one problem planted. It's a skills demonstration of contribution analysis, the method I'd apply to any KPI. |
| 0:40–1:05 | `sla_by_week.png` and `01_weekly_topline.sql` | This is what leadership sees: the top-line SLA barely moves. The problem is hidden in the average. |
| 1:05–1:35 | `02_sla_change_by_segment.sql` | Every site and queue, with how many points of the overall change each explains. One stands out: Account Takeover at Manila with Vendor B, from 97.4% to 74.0% from week 8, the largest contribution at −1.84 points. |
| 1:35–2:05 | `03_segment_drivers.sql` | Inside that segment: demand was flat, up 1.5%. Handle time rose 38% as new hires took up to 74% of contacts, and workload reached 117% of contracted hours. |
| 2:05–2:30 | `04_aht_by_tenure.sql` | That sizes the effect: new hires average 867 seconds per contact, against 541 for tenured specialists. |
| 2:30–2:45 | `rca/analyze.py`, then `output/report.md` | The change week is detected automatically, and the report text is generated from the query results, including what the data can't tell us. Nothing about the answer is hard-coded. |
| 2:45–3:00 | Back to the README top | For an operations leader, that's the cause, its size and the fix, before the next weekly review. Links are under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `python -m rca.generate` and `python -m rca.analyze` once so the report and chart are fresh.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "synthetic" out loud when you introduce the data. This is a skills demonstration, not a rebuild of client work.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the walkthrough line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
