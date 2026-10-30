from rca.analyze import connect, find_change_week, query, run
from rca.generate import INCIDENT_WEEK, generate


def test_change_week_detects_step_down():
    rows = [{"week": w, "sla_pct": 95.0 if w < 6 else 80.0} for w in range(1, 11)]
    assert find_change_week(rows) == 6


def test_analysis_finds_planted_root_cause(tmp_path):
    data = generate(tmp_path / "data")
    answer = run(data, tmp_path / "out")

    assert "Account Takeover at Manila (Vendor B)" in answer
    assert f"from week {INCIDENT_WEEK}" in answer
    assert (tmp_path / "out" / "report.md").exists()
    assert (tmp_path / "out" / "sla_by_week.png").exists()


def test_segment_contributions_cover_every_segment(tmp_path):
    con = connect(generate(tmp_path / "data"))
    segments = query(con, "02_sla_change_by_segment.sql", change_week=INCIDENT_WEEK)
    assert len(segments) == 12  # 4 sites x 3 queues
    assert segments[0]["site"] == "Manila"  # sorted worst contribution first
