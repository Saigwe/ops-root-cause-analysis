-- Which site x queue segment moved SLA? Compare the baseline period with the recent period, and quantify each
-- segment's contribution to the change in overall SLA (in percentage points of total contacts).
with periods as (
    select *, case when week >= $change_week then 'recent' else 'baseline' end as period
    from contacts
),

seg as (
    select
        site, vendor, queue, period,
        count(*)            as contacts,
        sum(within_sla)     as within_sla
    from periods
    group by all
),

totals as (
    select period, sum(contacts) as all_contacts from seg group by period
),

wide as (
    select
        s.site, s.vendor, s.queue,
        max(case when s.period = 'baseline' then 100.0 * s.within_sla / s.contacts end) as sla_baseline,
        max(case when s.period = 'recent'   then 100.0 * s.within_sla / s.contacts end) as sla_recent,
        -- contribution = points of overall SLA "missed" by this segment in each period
        max(case when s.period = 'recent'   then 100.0 * s.within_sla / t.all_contacts end)
          - max(case when s.period = 'baseline' then 100.0 * s.within_sla / t.all_contacts end)
          as contribution_pts
    from seg as s
    join totals as t using (period)
    group by all
)

select
    site, vendor, queue,
    round(sla_baseline, 1)                   as sla_baseline_pct,
    round(sla_recent, 1)                     as sla_recent_pct,
    round(sla_recent - sla_baseline, 1)      as sla_change_pts,
    round(contribution_pts, 2)               as contribution_to_overall_pts
from wide
order by contribution_to_overall_pts
