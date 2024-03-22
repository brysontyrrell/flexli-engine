import json
from datetime import datetime, timedelta
import random
import string

import dateutil.parser
import jmespath.functions

import flexli_globals


class CustomFunctionException(Exception):
    pass


class FlexliCustomFunctions(jmespath.functions.Functions):
    @jmespath.functions.signature()
    def _func_flexli_iterator_value(self):
        # TODO: Returns iterator value for a running workflow
        # But how?
        if flexli_globals.ITERATOR_VALUE is None:
            raise CustomFunctionException("No iterator value present")
        else:
            return flexli_globals.ITERATOR_VALUE

    @jmespath.functions.signature()
    def _func_flexli_datetime_now(self) -> str:
        return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

    @jmespath.functions.signature({"types": ["string"]})
    def _func_flexli_datetime(self, date_format: str) -> str:
        """%Y-%m-%dT%H:%M:%SZ"""
        return datetime.utcnow().strftime(date_format)

    @jmespath.functions.signature(
        {"types": ["string"]}, {"types": ["string"]}, {"types": ["number"]}
    )
    def _func_flexli_time_delta(
        self, base_datetime: str, date_format: str, delta_minutes: int
    ):
        parsed_datetime = dateutil.parser.parse(base_datetime)
        return (parsed_datetime + timedelta(minutes=delta_minutes)).strftime(
            date_format
        )

    def _func_flexli_source_datetime(self, date_format: str):
        """Return a timestamp for source of the workflow."""

    def _func_flexli_start_datetime(self, date_format: str):
        """Return a timestamp for start of the workflow run."""

    @jmespath.functions.signature({"types": ["array"]}, {"types": ["array"]})
    def _func_flexli_diff_arrays(self, previous_array: list, current_array: list):
        """Compares 'current_array' to 'previous_array'.

        Elements in 'current_array' not  in 'previous_array' are returned in the 'added' list.
        Elements in 'previous_array' not  in 'current_array' are returned in the 'removed' list.

        Use in JMESPath expressions be calling 'flexli_diff_arrays()'.
        """
        return {
            "added": [i for i in current_array if i not in previous_array],
            "removed": [i for i in previous_array if i not in current_array],
        }

    @jmespath.functions.signature(
        {"types": ["number"]}, {"types": ["string"], "variadic": True}
    )
    def _func_flexli_random_string(self, length: int, *args: list[str]):
        """Generates a random string."""
        character_set = ""

        if "lowercase" in args:
            character_set += string.ascii_lowercase

        if "uppercase" in args:
            character_set += string.ascii_uppercase

        if "numbers" in args:
            character_set += string.digits

        return "".join(random.choice(character_set) for _ in range(length))

    @jmespath.functions.signature({"types": ["object", "array"]})
    def _func_flexli_to_json_string(self, obj: dict | list) -> str:
        return json.dumps(obj)


flexli_options = jmespath.Options(custom_functions=FlexliCustomFunctions())
