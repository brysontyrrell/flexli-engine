from pydantic import AnyUrl, constr


WorkflowV1Type = constr(regex="^[a-zA-Z0-9]+$")


class HttpsUrl(AnyUrl):
    allowed_schemes = {"https"}
    tld_required = True
    max_length = 2083
