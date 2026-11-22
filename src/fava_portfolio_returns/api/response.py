import functools
import json
import traceback
from dataclasses import fields
from dataclasses import is_dataclass
from datetime import date
from decimal import Decimal

from beancount import Amount
from fava.helpers import FavaAPIError
from flask import Response


def _json_data(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Amount):
        return {"number": _json_data(value.number), "currency": value.currency}
    if is_dataclass(value):
        return {field.name: _json_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {key: _json_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_data(item) for item in value]
    return value


def api_response(func):
    """return {success: true, data: ...} or {success: false, error: ...}"""

    @functools.wraps(func)
    def decorator(*args, **kwargs) -> Response:
        try:
            data = func(*args, **kwargs)
            return Response(json.dumps({"success": True, "data": _json_data(data)}), mimetype="application/json")
        except FavaAPIError as e:
            return Response(json.dumps({"success": False, "error": e.message}), status=500, mimetype="application/json")
        except Exception as e:  # pylint: disable=broad-exception-caught
            traceback.print_exception(e)
            return Response(json.dumps({"success": False, "error": str(e)}), status=500, mimetype="application/json")

    return decorator
