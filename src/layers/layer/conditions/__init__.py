from datetime import date, datetime, timedelta
from typing import Iterable

import dateutil.parser
from dateutil.tz import tzutc
from dateutil.utils import default_tzinfo
import jmespath

from .models import Condition, Criteria, CriteriaAttributes


class ConditionEvaluator:
    def __init__(self, condition: dict):
        self.model = Condition.model_validate(condition)
        self.criteria = [CriteriaEvaluator(c) for c in self.model.criteria]

    def evaluate(self, resource: dict) -> bool:
        if self.model.operator == "and":
            return all([a.evaluate(resource) for a in self.criteria])
        elif self.model.operator == "or":
            return any([a.evaluate(resource) for a in self.criteria])


class CriteriaEvaluator:
    def __init__(self, model: Criteria):
        self.model = model
        self.attributes = [AttributeEvaluator(a) for a in model.attributes]

    def evaluate(self, resource: dict) -> bool:
        if self.model.operator == "and":
            return all([a.evaluate(resource) for a in self.attributes])
        elif self.model.operator == "or":
            return any([a.evaluate(resource) for a in self.attributes])


class AttributeEvaluator:
    def __init__(self, model: CriteriaAttributes):
        self.model = model
        self.value = self.model.value
        self.operator = getattr(self, f"{model.operator}_")

    def __repr__(self) -> str:
        return f"<Attribute: '{self.model.attribute}' {self.model.operator} '{self.value}'>"

    def evaluate(self, resource: dict) -> bool:
        """Validate that the values returned at the resource's 'attribute' evaluate to
        'True' when compared to the set 'operator' and 'value.'

        The 'operator' will map to a method that implements it:
          * eq -> eq_()
          * before -> before_()

        No returned values for the 'attribute' will return 'False.'

        'TypeError' exceptions thrown by a mismatch between the type of the returned
        value and the type of the matching value will return 'False.'
        """
        if not (attr_values := self._find_values(resource, self.model.attribute)):
            return False
        try:
            self.operator(
                attr_values=attr_values,
                value_to_compare=self._evaluator_value(resource),
            )
        except (AssertionError, TypeError, AttributeError) as error:
            # TODO: This is way too broad
            print(error)
            return False
        else:
            return True

    def _evaluator_value(self, source: dict):
        """If 'value' is a JMESPath expression search and return that path."""
        if isinstance(self.value, str) and self.value.startswith("::"):
            result = jmespath.search(self.value[2:], source)
            # This should trigger validation and cast to the correct type!
            self.model.value = result
            self.value = self.model.value

        return self.value

    @staticmethod
    def _find_values(source: dict, expression: str) -> tuple:
        """'expression' will begin with '::'"""
        values = jmespath.search(expression[2:], source)
        if isinstance(values, Iterable) and not isinstance(values, str):
            return tuple(values)
        else:
            return tuple((values,))

    @staticmethod
    def eq_(attr_values: tuple, value_to_compare) -> None:
        """At least one of the resource values must equal the matching value"""
        assert any([v == value_to_compare for v in attr_values])

    @staticmethod
    def ne_(attr_values: tuple, value_to_compare) -> None:
        """None of the resource values can equal the matching value."""
        assert all([v != value_to_compare for v in attr_values])

    @staticmethod
    def lt_(attr_values: tuple, value_to_compare) -> None:
        assert any([v < value_to_compare for v in attr_values])

    @staticmethod
    def gt_(attr_values: tuple, value_to_compare) -> None:
        assert any([v > value_to_compare for v in attr_values])

    @staticmethod
    def lte_(attr_values: tuple, value_to_compare) -> None:
        assert any([v <= value_to_compare for v in attr_values])

    @staticmethod
    def gte_(attr_values: tuple, value_to_compare) -> None:
        assert any([v >= value_to_compare for v in attr_values])

    @staticmethod
    def starts_with_(attr_values: tuple[str, ...], value_to_compare) -> None:
        """String only operator method."""
        assert any([v.startswith(value_to_compare) for v in attr_values])

    @staticmethod
    def offset_datetime(days_ago=0) -> datetime:
        """Return timezone aware UTC datetime object offset by X days in the past."""
        return (datetime.utcnow() - timedelta(days=days_ago)).replace(tzinfo=tzutc())

    @staticmethod
    def make_datetime(timestamp) -> datetime:
        """Converts an epoch or ISO 8601 date string to a UTC datetime object.

        Jamf Pro stores epoch timestamps as 13 digit integers and not floats. These
        values have to be converted to floats before conversion.
        """
        if isinstance(timestamp, datetime):
            date_obj = timestamp
        elif isinstance(timestamp, date):
            date_obj = datetime.fromordinal(timestamp.toordinal())
        elif isinstance(timestamp, (int, float)):
            date_obj = (
                datetime.utcfromtimestamp(timestamp / 1000)
                if timestamp > 1000000000000
                else datetime.utcfromtimestamp(timestamp)
            )
        else:
            date_obj = dateutil.parser.parse(timestamp)
        return default_tzinfo(date_obj, tzutc())

    def before_(self, attr_values: tuple, value_to_compare) -> None:
        """Date only operator method.
        Assert the resource value timestamp occurs before the 'Value' timestamp.
        """
        assert any(
            [
                self.make_datetime(v) <= self.make_datetime(value_to_compare)
                for v in attr_values
            ]
        )

    def after_(self, attr_values: tuple, value_to_compare) -> None:
        """Date only operator method.
        Assert the resource value timestamp occurs after the 'Value' timestamp.
        """
        assert any(
            [
                self.make_datetime(v) > self.make_datetime(value_to_compare)
                for v in attr_values
            ]
        )

    def less_than_x_days_(self, attr_values: tuple, value_to_compare) -> None:
        """Compares the timestamp values against the current date offset by a number of
        days (the 'Value'). Asserts 'True' if the value is later than (greater than)
        the offset time.
        """
        # TODO: Implement
        print(attr_values)
        print(repr(self.make_datetime(attr_values[0])))
        print(repr(self.offset_datetime(value_to_compare)))
        assert any(
            [
                self.make_datetime(v) > self.offset_datetime(value_to_compare)
                for v in attr_values
            ]
        )

    def more_than_x_days_(self, attr_values: tuple, value_to_compare) -> None:
        """Compares the timestamp values against the current date offset by a number of
        days (the 'Value'). Asserts 'True' if the value is earlier than (less than) the
        offset time.
        """
        # TODO: Implement
        assert any(
            [
                self.make_datetime(v) < self.offset_datetime(value_to_compare)
                for v in attr_values
            ]
        )


def evaluate_condition(condition: dict, source: dict) -> bool:
    condition_evaluator = ConditionEvaluator(condition)
    return condition_evaluator.evaluate(source)
