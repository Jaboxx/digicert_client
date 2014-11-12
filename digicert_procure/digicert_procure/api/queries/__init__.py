#!/usr/bin/env python

from ...api import Action


class Query(Action):
    """Base class for CQRS-style Query objects."""
    def __init__(self, customer_api_key, customer_name=None, **kwargs):
        super(Query, self).__init__(customer_api_key=customer_api_key, customer_name=customer_name, **kwargs)

    def get_method(self):
        return 'GET'


if __name__ == '__main__':
    pass