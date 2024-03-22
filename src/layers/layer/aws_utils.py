from functools import lru_cache
from typing import Optional

import boto3


@lru_cache
def get_boto3_session(region_name: Optional[str] = None):
    return boto3.Session(region_name=region_name)


@lru_cache
def get_boto3_client(service_name: str, session: Optional[boto3.Session] = None):
    if not session:
        session = get_boto3_session()
    return session.client(service_name)


@lru_cache
def get_boto3_resource(service_name: str, session: Optional[boto3.Session] = None):
    if not session:
        session = get_boto3_session()
    return session.resource(service_name)
