import jmespath

from transforms import flexli_options


"""
import sys
sys.path.append("src/layers/layer")
from transforms import jmespath, flexli_options

jmespath.search("flexli_to_json_string(@)", {"foo": "bar"}, options=flexli_options)

jmespath.search("flexli_datetime_now()", {}, options=flexli_options)
jmespath.search("flexli_datetime(`%Y-%m-%dT%H:%M:%SZ`)", {}, options=flexli_options)

jmespath.search("flexli_time_delta(flexli_datetime_now(), `%Y-%m-%dT%H:%M:%SZ`, `15`)", {}, options=flexli_options)
jmespath.search("flexli_time_delta(flexli_datetime(`%Y-%m-%dT%H:%M:%SZ`), `%Y-%m-%dT%H:%M:%SZ`, `-15`)", {}, options=flexli_options)


"""


def test_datetime_isoformat():
    pass
