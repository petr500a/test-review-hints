class Bus:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)

    def get_all(self):
        return list(self.events)


def test_bus_transport():
    bus = Bus()
    bus.emit("loaded")
    assert bus.get_all() == ["loaded"]
