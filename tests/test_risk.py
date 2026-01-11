from risk.position_sizing import RiskManager
from risk.stop_loss import fixed_percentage_stop
from risk.take_profit import fixed_rr_take_profit


def main():
    balance = 10000
    risk_pct = 0.01
    entry = 100
    direction = "BUY"

    stop = fixed_percentage_stop(entry, 0.01, direction)
    tp = fixed_rr_take_profit(entry, stop, 2, direction)

    rm = RiskManager()
    size = rm.calculate_position_size(balance, risk_pct, entry, stop)

    print("Entry:", entry)
    print("Stop Loss:", stop)
    print("Take Profit:", tp)
    print("Position Size:", size)


if __name__ == "__main__":
    main()
