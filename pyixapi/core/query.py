import json

from pyixapi.core.util import cat


class RequestError(Exception):
    """
    More detailed exception that returns the original requests object for inspection.
    Along with some attributes with specific details from the requests object. If
    return is JSON we decode and add it to the message.
    """

    def __init__(self, r):
        if r.status_code == 404:
            self.message = f"The requested url: {r.url} could not be found."
        elif r.status_code == 401:
            self.message = (
                "Authentication credentials are invalid, tokens renewal required."
            )
        else:
            try:
                self.message = f"The request failed with code {r.status_code} {r.reason}: {r.json()}"
            except ValueError:
                self.message = f"The request failed with code {r.status_code} {r.reason} but details were not found as JSON."

        super(RequestError, self).__init__(r)
        self.req = r
        self.error = r.text

    def __str__(self):
        return self.message


class ContentError(Exception):
    """
    Raised If the API URL does not point to a valid IX-API API, the server may return
    a valid response code, but the content is not JSON. This exception is raised in
    those cases.
    """

    def __init__(self, req):
        super(ContentError, self).__init__(req)

        self.req = req
        self.error = (
            "The server returned invalid (non-JSON) data. Maybe not an IX-API server?"
        )

    def __str__(self):
        return self.error


class Request(object):
    """
    Create requests to the IX-API.

    Responsible for building the URL and making the HTTP(S) requests to the API.

    :param base: (str) Base URL passed in api() instantiation.
    :param filters: (dict, optional) contains key/value pairs that correlate to the
        filters a given endpoint accepts.
        In (e.g. /api/v1/devices?name='test') 'name': 'test' would be in the filters
        dict.
    """

    def __init__(
        self, base, http_session, filters=None, key=None, token=None, user_agent=None
    ):
        self.base = base
        self.filters = filters or None
        self.key = key
        self.token = token
        self.http_session = http_session
        self.url = self.base if not key else cat(self.base, key)
        self.user_agent = user_agent

    def get_openapi(self):
        """
        Get the OpenAPI Spec.
        """
        headers = {"Content-Type": "application/json;"}
        req = self.http_session.get(
            cat(self.base, "docs/?format=openapi"), headers=headers
        )
        if req.ok:
            return req.json()
        else:
            raise RequestError(req)

    def get_version(self):
        """
        Get the API version of IX-API.

        Issue a GET request to the health endpoint to read the API version.

        If a RequestError is raised, it is catched and the version is considered as
        equal to 1 (IX-API v1 does not have a health endpoint).
        """
        try:
            return self.get_health()["version"]
        except RequestError:
            return "1"

    def get_health(self):
        """
        Get the health from /api/health endpoint in IX-API.
        """
        headers = {"Content-Type": "application/json;"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        r = self.http_session.get(cat(self.base, "health"), headers=headers)
        if r.ok:
            return r.json()
        else:
            raise RequestError(r)

    def _make_call(self, verb="get", url_override=None, add_params=None, data=None):
        if verb in ("post", "put") or verb == "delete" and data:
            headers = {"Content-Type": "application/json;"}
        else:
            headers = {"accept": "application/json;"}

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        params = {}
        if not url_override:
            if self.filters:
                params.update(self.filters)
            if add_params:
                params.update(add_params)

        r = getattr(self.http_session, verb)(
            url_override or self.url, headers=headers, params=params, json=data
        )

        if verb == "delete":
            if r.ok:
                return True
            else:
                raise RequestError(r)
        elif r.ok:
            try:
                return r.json()
            except json.JSONDecodeError:
                raise ContentError(r)
        else:
            raise RequestError(r)

    def get(self, add_params=None):
        """
        Make a GET request to IX-API.

        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.

        :Returns: List of `Response` objects returned from the endpoint.
        """

        req = self._make_call(add_params=add_params)
        if isinstance(req, list):
            self.count = len(req)
            for i in req:
                yield i
        else:
            self.count = len(req)
            yield req

    def put(self, data):
        """
        Make a PUT request to IX-API.

        :param data: (dict) Contains a dict that will be turned into a JSON object and
            sent to the API.
        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not json.
        :returns: Dict containing the response from IX-API.
        """
        return self._make_call(verb="put", data=data)

    def post(self, data):
        """
        Make a POST request to IX-API.

        :param data: (dict) Contains a dict that will be turned into a JSON object and
            sent to the API.
        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.
        :Returns: Dict containing the response from IX-API.
        """
        return self._make_call(verb="post", data=data)

    def delete(self, data=None):
        """
        Make a DELETE request to IX-API.

        :param data: (list) Contains a dict that will be turned into a JSON object and
            sent to the API.
        Returns:
            True if successful.

        Raises:
            RequestError if req.ok doesn't return True.
        """
        return self._make_call(verb="delete", data=data)

    def patch(self, data):
        """
        Make a PATCH request to IX-API.

        :param data: (dict) Contains a dict that will be turned into a JSON object and
            sent to the API.
        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.
        :returns: Dict containing the response from IX-API.
        """
        return self._make_call(verb="patch", data=data)

    def options(self):
        """
        Make an OPTIONS request to IX-API.

        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.

        :returns: Dict containing the response fromIX-API.
        """
        return self._make_call(verb="options")
