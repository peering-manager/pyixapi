import json
from http import HTTPStatus
from typing import Any

from pyixapi.core.util import cat


class RequestError(Exception):
    """
    More detailed exception that returns the original requests object for inspection.
    Along with some attributes with specific details from the requests object. If
    return is JSON we decode and add it to the message.
    """

    def __init__(self, r) -> None:
        if r.status_code == HTTPStatus.NOT_FOUND:
            self.message = f"The requested url: {r.url} could not be found."
        elif r.status_code == HTTPStatus.UNAUTHORIZED:
            self.message = (
                "Authentication credentials are invalid, tokens renewal required."
            )
        else:
            try:
                self.message = (
                    f"The request failed with code {r.status_code} "
                    f"{r.reason}: {r.json()}"
                )
            except ValueError:
                self.message = (
                    f"The request failed with code {r.status_code} "
                    f"{r.reason} but details were not found as JSON."
                )

        super().__init__(r)
        self.req = r
        self.error = r.text

    def __str__(self) -> str:
        return self.message


class ContentError(Exception):
    """
    Raised If the API URL does not point to a valid IX-API API, the server may return
    a valid response code, but the content is not JSON. This exception is raised in
    those cases.
    """

    def __init__(self, req) -> None:
        super().__init__(req)

        self.req = req
        self.error = (
            "The server returned invalid (non-JSON) data. Maybe not an IX-API server?"
        )

    def __str__(self) -> str:
        return self.error


class Request:
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
    ) -> None:
        self.base = base
        self.filters = filters or None
        self.key = key
        self.token = token
        self.http_session = http_session
        self.url = self.base if not key else cat(self.base, key)
        self.user_agent = user_agent

    def get_openapi(self) -> Any:
        """
        Get the OpenAPI Spec.
        """
        headers = {"Content-Type": "application/json;"}
        req = self.http_session.get(
            cat(self.base, "docs/?format=openapi"), headers=headers
        )
        if req.ok:
            return req.json()

        raise RequestError(req)

    def get_version(self) -> int:
        """
        Get the API version of IX-API.

        Issue a GET request to the health endpoint to read the API version.

        If a RequestError is raised, it is catched and the version is considered as
        equal to 1 (IX-API v1 does not have a health endpoint).
        """
        try:
            return int(self.get_health()["version"])
        except RequestError:
            return 1

    def get_health(self) -> dict[str, Any]:
        """
        Get the health from /api/health endpoint in IX-API.
        """
        headers = {"Content-Type": "application/json;"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        r = self.http_session.get(cat(self.base, "health"), headers=headers)
        if r.ok:
            return r.json()

        raise RequestError(r)

    def _make_call(
        self,
        verb: str = "get",
        url_override: str | None = None,
        add_params: dict[str, Any] | None = None,
        data: Any | None = None,
    ) -> Any:
        if verb in {"post", "put"} or verb == "delete" and data:
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

            raise RequestError(r)
        if r.ok:
            try:
                return r.json()
            except json.JSONDecodeError as e:
                raise ContentError(r) from e
        else:
            raise RequestError(r)

    def get(self, add_params: dict[str, Any] | None = None) -> Any:
        """
        Make a GET request to IX-API.

        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.

        :Returns: List of `Response` objects returned from the endpoint.
        """

        req = self._make_call(add_params=add_params)
        if isinstance(req, list):
            self.count = len(req)
            yield from req
        else:
            self.count = len(req)
            yield req

    def put(self, data: Any) -> Any:
        """
        Make a PUT request to IX-API.

        :param data: (dict) Contains a dict that will be turned into a JSON object and
            sent to the API.
        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not json.
        :returns: Dict containing the response from IX-API.
        """
        return self._make_call(verb="put", data=data)

    def post(self, data: Any) -> Any:
        """
        Make a POST request to IX-API.

        :param data: (dict) Contains a dict that will be turned into a JSON object and
            sent to the API.
        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.
        :Returns: Dict containing the response from IX-API.
        """
        return self._make_call(verb="post", data=data)

    def delete(self, data: Any | None = None) -> Any:
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

    def patch(self, data: Any) -> Any:
        """
        Make a PATCH request to IX-API.

        :param data: (dict) Contains a dict that will be turned into a JSON object and
            sent to the API.
        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.
        :returns: Dict containing the response from IX-API.
        """
        return self._make_call(verb="patch", data=data)

    def options(self) -> Any:
        """
        Make an OPTIONS request to IX-API.

        :raises: RequestError if req.ok returns false.
        :raises: ContentError if response is not JSON.

        :returns: Dict containing the response fromIX-API.
        """
        return self._make_call(verb="options")
