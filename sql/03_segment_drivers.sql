-- Inside the worst segment: is the cause staffing mix (tenure), handle time, or demand?
-- Occupancy = handled seconds / contracted staffed seconds (38,000 per site-queue-day).
select
    week,
    count(*) / 7.0                                                        as contacts_per_day,
    round(avg(handle_seconds))                                            as aht_seconds,
    round(100.0 * avg(case when tenure_weeks < 4 then 1 else 0 end), 1)   as pct_contacts_new_hires,
    count(distinct specialist_id)                                         as active_specialists,
    round(100.0 * sum(handle_seconds) / (7 * 38000.0), 1)                 as occupancy_pct,
    round(avg(wait_seconds) / 60.0, 1)                                    as avg_wait_minutes,
    round(100.0 * avg(within_sla), 1)                                     as sla_pct
from contacts
where site = $site and queue = $queue
group by week
order by week
