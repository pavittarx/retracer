import pandas as pd;
import datetime as datetime;

import yfinance as yf;

from modules.positions import Positions
from modules.backtester import Backtest

import numpy as np

# Configuration
ticker=''
period=''

class Tester(Backtest):
    ticker_data = None
    count = 0
    close_count = 0
    stats = {}

    def __init__(self, balance, stoploss, reward_ratio):
        super().__init__(balance, stoploss, reward_ratio)
        self.ticker_data = None
        self.reset_tradebook()

        self.profitable_trades = None
        self.losing_trades = None

    def init(self, ticker_data, size, small_ema, large_ema):
        ticker_data["small_ema"] = (
            ticker_data["Close"].ewm(span=small_ema, adjust=False).mean()
        )

        ticker_data["large_ema"] = (
            ticker_data["Close"].ewm(span=large_ema, adjust=False).mean()
        )

        ticker_data["crossover_pos"] = np.where(
            ticker_data["small_ema"] > ticker_data["large_ema"], "short", "long"
        )

        ticker_data["crosspoint"] = np.where(
            ticker_data["crossover_pos"] != ticker_data["crossover_pos"].shift(1),
            True,
            False,
        )

        self.small_ema = small_ema
        self.large_ema = large_ema
        self.ticker_data = None
        self.ticker_data = ticker_data
        self.size = size

    def load_data(self, data):
        self.ticker_data = data
    
    def print(self):
        print(self.position)

    def run(self):
        if self.ticker_data is None:
            raise Exception("No ticker data to run backtest on")

        # Skip first 200 candles
        start_index = self.large_ema

        print("Start Index", start_index, len(self.ticker_data))

        while start_index < len(self.ticker_data):
            self.strategy(self.ticker_data.iloc[start_index])
            start_index += 1
            
        self.calc_stats()

    def calc_stats(self):
        crosspoints = len(
            self.ticker_data[self.large_ema :][self.ticker_data["crosspoint"] == True]
        )
        
        total_trades = len(self.trade_book)
        profitable_trades = self.trade_book[self.trade_book["PnL"] > 0]
        losing_trades = self.trade_book[self.trade_book["PnL"] < 0]
        win_percentage = len(profitable_trades) / total_trades * 100
        lose_percentage = len(losing_trades) / total_trades * 100
        
        self.stats = {
            **self.stats,
            "date_range": f'{self.trade_book["entry_date"].iloc[0]} - {self.trade_book["exit_date"].iloc[-1]}',
            "open_positions": self.positions.count(),
            "open_counter": self.count,
            "close_counter": self.close_count,
            "total_trades": total_trades,
            "crosspoints_count": crosspoints,
            "small_ema": self.small_ema,
            "large_ema": self.large_ema,
            "total_trades": len(self.trade_book),
            "pnl": self.trade_book["PnL"].sum(),
            "initial_balance": self.start_balance,
            "trade_size": self.size,
            "stoploss": self.stoploss,
            "target": self.target,
            "profitable_trades": profitable_trades,
            "losing_trades": losing_trades,
            "profitable_trades_count": len(profitable_trades),
            "losing_trades_count": len(losing_trades),
            "win_percentage": win_percentage,
            "lose_percentage": lose_percentage,
            "date_range": f'{self.trade_book["entry_date"].iloc[0]} - {self.trade_book["exit_date"].iloc[-1]}',
        }

    def check_position(self, position, candle):
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

    def strategy(self, candle):
        if self.positions.count() > 0:
            # check if target met or stoploss hit
            # calculate trade results, PnL
            # close position

            for position in self.positions.get_positions():
                exit_price = self.check_position(position, candle)

                closed = False
                next_candle = candle

                if candle["i"] < len(ticker_data) - 1:
                    next_candle = self.ticker_data.iloc[candle["i"] + 1]

                if exit_price is not None:
                    sl_candles = yf.download(
                        ticker,
                        start=position["entry_date"],
                        end=next_candle["dt"],
                        interval=sl_timeframe,
                        progress=False,
                    )

                    for i in range(len(sl_candles)):
                        c = sl_candles.iloc[i]

                        sl_exit = self.check_position(position, c)

                        if sl_exit is not None and sl_exit["type"] == "sl":
                            self.close_count = self.close_count + 1
                            self.close(position, candle, exit_price["price"])
                            closed = True
                            break

                    if not closed and exit_price["type"] == "tp":
                        self.close_count = self.close_count + 1
                        self.close(position, candle, exit_price["price"])


        if candle["crosspoint"] == True:
            entry_price = candle["Close"]
            crossover_type = "long" if candle["crossover_pos"] == 1 else "short"
            stoploss = None
            target = None

            self.count = self.count + 1

            if crossover_type == "short":
                stoploss = entry_price + self.stoploss
                target = entry_price - self.target

            if crossover_type == "long":
                stoploss = entry_price - self.stoploss
                target = entry_price + self.target

            self.open(
                entry_date=candle.name,
                entry_price=entry_price,
                stoploss=stoploss,
                target=target,
                size=self.size,
                crossover_type=crossover_type,
            )