"""Pure tier maths. No Frappe imports, so it can be unit-tested anywhere.

A "tier" is (up_to_day, pay_fraction), counted cumulatively over the leave year:
    Sick Leave:      [(15, 1.0), (45, 0.5), (90, 0.0)]
    Maternity Leave: [(45, 1.0), (60, 0.5), (105, 0.0)]
"""
from collections import defaultdict


def split_by_tier(leave_days, tiers):
    """leave_days: [(date, day_fraction)] sorted by date, for the WHOLE leave year.
    Returns [(date, {pay_fraction: days})]. Days past the last tier use the last tier's pay."""
    if not tiers:
        return [(d, {}) for d, _ in leave_days]
    
    out, used = [], 0.0        
    for d, frac in leave_days:
        buckets = defaultdict(float)
        start, end, prev = used, used + frac, 0.0
        for up_to, pay in tiers:
            overlap = max(0.0, min(end, up_to) - max(start, prev))
            if overlap:
                buckets[pay] += overlap
            prev = up_to
        beyond = end - max(start, prev)
        if beyond > 1e-9:
            buckets[tiers[-1][1]] += beyond
        out.append((d, dict(buckets)))
        used = end
    return out


def sum_in_period(split, start, end):
    """Add up {pay_fraction: days} for the dates inside [start, end]."""
    total = defaultdict(float)
    for d, buckets in split:
        if start <= d <= end:
            for pay, days in buckets.items():
                total[pay] += days
    return dict(total)
