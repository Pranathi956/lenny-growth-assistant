from app.routers.chat import _routing_decision


def test_routes_to_ship30_on_keyword():
    assert _routing_decision("Can you turn this into an essay for Ship 30?") == "ship30_essay"


def test_routes_to_qa_by_default():
    assert _routing_decision("What did they say about activation metrics?") == "grounded_qa"
