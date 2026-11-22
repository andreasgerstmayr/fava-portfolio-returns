from datetime import date
from decimal import Decimal

from beancount import Amount

from fava_portfolio_returns.api.portfolio import PortfolioValue
from fava_portfolio_returns.api.response import api_response


def test_api_response_serializes_portfolio_data():
    @api_response
    def endpoint():
        return {
            "valueChart": [PortfolioValue(date(2020, 6, 1), Decimal("70.25"), Decimal("35.50"), Decimal("36.75"))],
            "units": (Amount(Decimal("2.5"), "CORP"),),
        }

    response = endpoint()

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.get_json() == {
        "success": True,
        "data": {
            "valueChart": [{"date": "2020-06-01", "market": 70.25, "cost": 35.5, "cash": 36.75}],
            "units": [{"number": 2.5, "currency": "CORP"}],
        },
    }
