import pandas as pd
import datetime as datetime
import yfinance as yf

from modules.positions import Positions
from modules.backtester import Backtest

import numpy as np

import json

# Configuration``
ticker = ""
period = ""
balance=1000
sma_span = 8
lma_span = 40
threshold = 0.0003
stoploss = 0.1
reward_ratio = 5
size = 1

pd.set_option("display.max_rows", None, "display.max_columns", None)


def check_position(position, candle):
    if position["crossover_type"] == "long":
        if (
            candle["Low"] < position["stoploss"]
            and position["stoploss"] > candle["Close"]
        ):
            return {"price": candle["Close"], "type": "sl"}

        if candle["High"] > position["target"]:
            return {"price": position["target"], "type": "tp"}

    if position["crossover_type"] == "short":
        if (
            candle["High"] > position["stoploss"]
            and position["stoploss"] < candle["Close"]
        ):
            return {"price": candle["Close"], "type": "sl"}

        if candle["Low"] < position["target"]:
            return {"price": position["target"], "type": "tp"}

    return None


def check_signals(df, sma_span, lma_span, threshold):
    df["small_ema"] = df["Close"].ewm(span=sma_span, adjust=False).mean()

    df["large_ema"] = df["Close"].ewm(span=lma_span, adjust=False).mean()

    df["cross_diff"] = df["large_ema"] - df["small_ema"]

    df["crossover_type"] = np.where(df["cross_diff"] > 0, "long", "short")

    df["signal"] = False

    for i in range(1, len(df)):
        diff_n = abs(df["cross_diff"].iloc[i])
        diff_n1 = abs(df["cross_diff"].iloc[i - 1])

        if diff_n <= threshold and diff_n1 > threshold:
            df["signal"].iloc[i] = True

    df["dt"] = df.index

    return df


def pos_consolidator(positions, candle, close):
    # Checks & closes positions
    if not positions.count() > 0:
        return

    for position in positions.get_positions():
        exit_price = check_position(position, candle)

        if exit_price is not None:
            if exit_price is not None:
                close(position, candle, exit_price)


def opener(candle, params, open):
    # Checks & opens positions

    if candle["signal"] == True:
        entry_price = candle["Close"]
        stoploss = None
        target = None

        if candle["crossover_type"] == "short":
            stoploss = entry_price + params["sl"]
            target = entry_price - params["tgt"]

        if candle["crossover_type"] == "long":
            stoploss = entry_price - params["sl"]
            target = entry_price + params["tgt"]

        open(
            entry_date=candle['dt'],
            entry_price=entry_price,
            stoploss=stoploss,
            target=target,
            size=params["size"],
            crossover_type=candle["crossover_type"],
        )


class Tester(Backtest):
    ticker_data = None
    count = 0
    close_count = 0
    stats = {}

    def __init__(self, params):
        super().__init__(
            balance=params["balance"],
            stoploss=params["sl"],
            reward_ratio=params["reward_ratio"],
        )
        self.reset_tradebook()

    def load_data(self, data):
        self.ticker_data = data

    def run(self):
        if self.ticker_data is None:
            raise Exception("No ticker data to run backtest on")

        check_signals(self.ticker_data, sma_span, lma_span, threshold)

        # Skip first 200 candles
        start_index = lma_span

        while start_index < len(self.ticker_data) -1:
            candle = self.ticker_data.iloc[start_index]
            
            pos_consolidator(self.positions, candle, self.close)
            opener(
                candle,
                {
                    "sl": stoploss,
                    "tgt": reward_ratio * stoploss,
                    'size': size
                },
                self.open,
            )
            
            start_index = start_index + 1

        self.calc_stats()

    def calc_stats(self):
        crosspoints = len(
            self.ticker_data[lma_span :][self.ticker_data["signal"] == True]
        )
        
        # print("Trade Book", self.trade_book)

        total_trades = len(self.trade_book)
        profitable_trades = self.trade_book[self.trade_book["PnL"] > 0]
        losing_trades = self.trade_book[self.trade_book["PnL"] < 0]
        win_percentage = total_trades > 0 and len(profitable_trades) / total_trades * 100
        lose_percentage = total_trades > 0 and len(losing_trades) / total_trades * 100

        self.stats = {
            **self.stats,
            "date_range": total_trades > 0 and f'{self.trade_book["entry_date"].iloc[0]} - {self.trade_book["exit_date"].iloc[-1]}',
            "open_positions": self.positions.count(),
            "open_counter": self.count,
            "close_counter": self.close_count,
            "total_trades": total_trades,
            "crosspoints_count": crosspoints,
            "sma_span": sma_span,
            "lma_span": lma_span,
            "total_trades": len(self.trade_book),
            "pnl": self.trade_book["PnL"].sum(),
            "initial_balance": self.start_balance,
            "trade_size": size,
            "stoploss": self.stoploss,
            "target": self.target,
            "profitable_trades": profitable_trades,
            "losing_trades": losing_trades,
            "profitable_trades_count": len(profitable_trades),
            "losing_trades_count": len(losing_trades),
            "win_percentage": win_percentage,
            "lose_percentage": lose_percentage
        }


t = Tester({
    'sl': stoploss,
    'reward_ratio': reward_ratio,
    'balance': balance
    })

tdata = yf.download("EURUSD=X", period="10d", interval="15m")
tdata['dt'] = tdata.index
tdata['dx'] = tdata['dt'].apply(lambda x: int(round(x.timestamp() * 1000)))

print(tdata)

t.load_data(tdata)
t.run()

# print(t.stats)

tdata = t.ticker_data

tdata['dt'] = tdata['dt'].astype(str)

result = json.dumps({
    'candles': tdata.to_dict('records'),
    # 'stats': t.stats.to_dict('records'),
})

with open("public/data.json", "w") as outfile:
    outfile.write(result)