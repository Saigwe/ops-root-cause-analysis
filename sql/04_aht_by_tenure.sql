-- Handle time by tenure band in the worst segment, recent period only. Sizes the "new hire" effect.
select
    case
        when tenure_weeks < 4 then '0-4 weeks'
        when tenure_weeks < 8 then '4-8 weeks'
        else '8+ weeks'
    end                                         as tenure_band,
    count(*)                                    as contacts,
    round(avg(handle_seconds))                  as aht_seconds
from contacts
where site = $site and queue = $queue and week >= $change_week
group by tenure_band
order by tenure_band
