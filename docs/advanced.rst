Custom Sessions
===============

Custom sessions can be used to modify the default HTTP behavior. Below are a few examples, most of them from `here <https://hodovi.ch/blog/advanced-usage-python-requests-timeouts-retries-hooks/>`_.

Headers
*******

To set a custom header on all requests. These headers are automatically merged with headers pyixapi sets itself.

:Example:

>>> import pyixapi
>>> import requests
>>> session = requests.Session()
>>> session.headers = {"mycustomheader": "test"}
>>> ixapi = pyixapi.api(
...     "https://api.de-cix.net/api/v1/",
...     "3LH3G72VH7H1SGogEsFeQOPsGjOQotMUZQRt2pK7YbH",
...     "cEtrt8s0vR0CsG0vpAmcaxtnolzZj7DEG0B7izvwPlV",
... )
>>> ixapi.http_session = session


SSL Verification
****************

To disable SSL verification. See `the docs <https://requests.readthedocs.io/en/stable/user/advanced/#ssl-cert-verification>`_.

:Example:

>>> import pyixapi
>>> import requests
>>> session = requests.Session()
>>> session.verify = False
>>> ixapi = pyixapi.api(
...     "https://api.de-cix.net/api/v1/",
...     "3LH3G72VH7H1SGogEsFeQOPsGjOQotMUZQRt2pK7YbH",
...     "cEtrt8s0vR0CsG0vpAmcaxtnolzZj7DEG0B7izvwPlV",
... )
>>> ixapi.http_session = session


Timeouts
********

Setting timeouts requires the use of Adapters.

:Example:

.. code-block:: python

    from requests.adapters import HTTPAdapter

    class TimeoutHTTPAdapter(HTTPAdapter):
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout", 5)
            super().__init__(*args, **kwargs)

        def send(self, request, **kwargs):
            kwargs['timeout'] = self.timeout
            return super().send(request, **kwargs)

    adapter = TimeoutHTTPAdapter()
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    ixapi = pyixapi.api(
        "https://api.de-cix.net/api/v1/",
        "3LH3G72VH7H1SGogEsFeQOPsGjOQotMUZQRt2pK7YbH",
        "cEtrt8s0vR0CsG0vpAmcaxtnolzZj7DEG0B7izvwPlV",
    )
    ixapi.http_session = session
