from pathlib import Path


def test_machine_specific_path():
    db_path = Path("C:/service/data/orders.db")
    assert db_path.name == "orders.db"


def test_fixture_path(tmp_path):
    db_path = tmp_path / "orders.db"
    assert db_path.name == "orders.db"
