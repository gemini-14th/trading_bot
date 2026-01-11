from data.validators import validate_trade


def main():
    valid = validate_trade(
        signal="BUY",
        trend="Bullish",
        entry=100,
        stop_loss=99,
        take_profit=102
    )

    invalid = validate_trade(
        signal="BUY",
        trend="Bearish",
        entry=100,
        stop_loss=99.5,
        take_profit=100.5
    )

    print("Valid trade:", valid)
    print("Invalid trade:", invalid)


if __name__ == "__main__":
    main()
