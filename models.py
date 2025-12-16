class Coffee:
    def __init__(self, name, price):
        self.name = name
        self.price = price


class Order:
    def __init__(self):
        self.items = []

    def add_item(self, coffee):
        self.items.append(coffee)

    def total(self):
        return sum(item.price for item in self.items)

    def clear(self):
        self.items.clear()
