def apply_discount(subtotal: float, is_vip: bool = False) -> float:
    """
    Single source of truth for discount rules.
    VIP gets +5 pp on top of any tier that applies (capped at 25%).
    """
    if subtotal > 1000:
        rate = 0.20
    elif subtotal > 500:
        rate = 0.10
    else:
        rate = 0.0

    if is_vip and rate > 0:
        rate = min(rate + 0.05, 0.25)

    return subtotal * (1 - rate)
