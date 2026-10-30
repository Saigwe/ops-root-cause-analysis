-- Top-line view leadership sees: weekly SLA, AHT and volume across every site and queue.
select
    week,
    count(*)                                  as contacts,
    round(100.0 * avg(within_sla), 1)         as sla_pct,
    round(avg(handle_seconds))                as aht_seconds
from contacts
group by week
order by week
