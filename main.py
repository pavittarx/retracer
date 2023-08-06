import pandas as pd
import datetime as datetime
import yfinance as yf

from modules.positions import Positions
from modules.backtester import Backtest

from setup.mongo import mgo
from pprint import pprint as log

import numpy as np

import json


# Configuration
ticker = "EURUSD=X"
period = ""
balance = 1000
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
            entry_date=candle["dt"],
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
        
        data = []
        
        for candle in self.ticker_data:
            c = candle['candle']
            
            
            
            c['dt'] = None
            c['signal'] = candle['signal']
            data.append(c)
            
        self.data = data    
        
        log(data[0])
        
t = Tester({"sl": stoploss, "reward_ratio": reward_ratio, "balance": balance})

data = mgo.candles.find()

t.load_data(data)
t.run()

data = t.ticker_data

result = json.dumps(
    {
        "candles": t.data,
        # 'stats': t.stats.to_dict('records'),
    }
)

with open("public/data.json", "w") as outfile:
    outfile.write(result)
