import pandas as pd
from .positions import Positions

class Backtest:
    balance = 0
    margin_used = 0
    start_balance = 0

    stoploss = 0
    target = 0

    positions = Positions()

    trade_book = pd.DataFrame(
        columns=[
            "entry_date",
            "entry_price",
            "exit_price",
            "exit_date",
            "target",
            "stoploss",
            "PnL",
            "crossover_type",
            "active",
            "size",
            "margin_used",
            "balance",
            "balance_on_open",
        ]
    )

    def __init__(self, balance, stoploss, reward_ratio):
        self.start_balance = balance
        self.balance = balance
        self.stoploss = stoploss
        self.target = stoploss * reward_ratio

        self.positions.clear_positions()
        self.reset_tradebook()

    def reset_tradebook(self):
        self.trade_book = pd.DataFrame(
            columns=[
                "entry_date",
                "entry_price",
                "exit_price",
                "exit_date",
                "target",
                "stoploss",
                "PnL",
                "crossover_type",
                "active",
                "size",
                "margin_used",
                "balance",
                "balance_on_open",
            ]
        )

    def open(self, entry_date, entry_price, stoploss, target, size, crossover_type):
        if self.balance is None or self.balance == 0:
            raise Exception("Oops, you ran out of bucks.")

        if self.balance < entry_price * size:
            print("Balance: ", self.balance)
            print("Lot Size: ", size)
            print("Ticket Price: ", entry_price * size)
            raise Exception("Oops, you are low on bucks.")

        position = {
            "entry_date": entry_date,
            "entry_price": entry_price,
            "stoploss": stoploss,
            "target": target,
            "size": size,
            "crossover_type": crossover_type,
            "margin_used": entry_price * size,
            "balance_on_open": self.balance - (entry_price * size),
        }

        self.margin_used = self.margin_used + (entry_price * size)

        self.positions.add_position(position)

        self.balance = self.balance - entry_price * size

    def close(self, position, candle, exit_price):
        # Open position is now closed & logged into the trade book
        trade = {
            **position,
            "exit_date": candle.name,
            "exit_price": exit_price,
        }

        trade["PnL"] = (exit_price - position["entry_price"]) * position["size"]

        if position["crossover_type"] == "short":
            trade["PnL"] = -1 * trade["PnL"]

        balance = self.balance + position["margin_used"] + trade["PnL"]
        trade["balance"] = balance
        self.balance = balance

        row = pd.Series(trade)
        self.trade_book.loc[len(self.trade_book)] = row

        self.positions.delete_position(position)