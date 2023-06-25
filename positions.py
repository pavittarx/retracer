import copy
import uuid


def updater(update):
    def update_position(position):
        return update if position.id == update.id else position


class Positions:
    positions = []

    def __init__(self):
        self.positions = []

    def get_positions(self):
        return self.positions

    def get_position(self, index):
        return self.positions[index]

    def get_position_by_id(self, id):
        return filter(lambda x: x["id"] == id, self.positions)

    def add_position(self, position):
        _position = {
            "id": uuid.uuid1(),
            "entry_date": position["entry_date"],
            "entry_price": position["entry_price"],
            "target": position["target"],
            "stoploss": position["stoploss"],
            "crossover_type": position["crossover_type"],
            "size": position["size"],
            "margin_used": position["margin_used"],
            "balance_on_open": position["balance_on_open"],
        }

        self.positions.append(_position)

    def count(self):
        return len(self.positions)

    def update_position(self, position):
        self.positions = map(updater(position), self.positions)

    def delete_position(self, position):
        self.positions = [
            _position
            for _position in self.positions
            if position["id"] != _position["id"]
        ]

    def clear_positions(self):
        self.positions = []
