class Item():
    """Stores information about an item."""

    def __init__(self, item_data):
        self.name = item_data["identifier"]
        self.id = item_data["id"]
        self.power = item_data["fling_power"]
        self.effect = item_data["fling_effect_id"]
