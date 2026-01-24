def calculate_sl_tp(entry, atr_pips, direction):
    SL_MULT = 2.0
    TP_MULT = 3.0

    sl_pips = atr_pips * SL_MULT
    tp_pips = atr_pips * TP_MULT

    if direction == "BUY":
        sl = entry - sl_pips
        tp = entry + tp_pips
    else:
        sl = entry + sl_pips
        tp = entry - tp_pips

    return sl, tp, sl_pips, tp_pips