from pyixapi.core.query import Request, RequestError
from pyixapi.core.response import Record, RecordSet
from pyixapi.core.util import cat


class Endpoint(object):
    """
    Represent actions available on endpoints in the IX-API.

    Build the correct URL to make queries and the proper :py:class:`.Response`
    object.
    """

    def __init__(self, api, name, model=None):
        self.return_obj = model if model else Record
        self.api = api
        self.url = cat(api.url, name)
        self.name = name

    def __str__(self):
        return self.url

    def all(self):
        """
        Return all objects from an endpoint.
        """
        r = Request(
            base=self.url,
            token=self.api.access_token,
            http_session=self.api.http_session,
        )
        return RecordSet(self, r)

    def filter(self, *args, **kwargs):
        """
        Query the list of a given endpoint. Also take named arguments that match the
        usable filters on a given endpoint.
        """
        r = Request(
            filters=kwargs,
            base=self.url,
            token=self.api.access_token,
            http_session=self.api.http_session,
        )
        return RecordSet(self, r)

    def get(self, *args, **kwargs):
        """
        Return a single object from an endpoint.
        """

        try:
            key = args[0]
        except IndexError:
            key = None

        if not key:
            response = self.filter(**kwargs)
            value = next(response, None)
            if not value:
                return value
            try:
                next(response)
                raise ValueError(
                    "get() returned more than one result. Check that the kwarg(s) passed are valid for this endpoint or use filter() or all() instead."
                )
            except StopIteration:
                return value

        r = Request(
            key=key,
            base=self.url,
            token=self.api.access_token,
            http_session=self.api.http_session,
        )
        try:
            return next(RecordSet(self, r), None)
        except RequestError as e:
            if e.req.status_code == 404:
                return None
            else:
                raise e
