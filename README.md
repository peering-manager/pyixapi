# pyixapi

Python API client library for [IX-API](https://ix-api.net/).

Supported versions are:

* [version 1](https://docs.ix-api.net/v1/)

## Installation

To install run `pip install pyixapi`.

Alternatively, you can clone the repo and run `python setup.py install`.

## Quick Start

To begin, import pyixapi and instantiate the API.

```python
import pyixapi
ixapi = pyixapi.api(
    "https://api.de-cix.net/api/v1/",
    "3LH3G72VH7H1SGogEsFeQOPsGjOQotMUZQRt2pK7YbH",
    "cEtrt8s0vR0CsG0vpAmcaxtnolzZj7DEG0B7izvwPlV",
)
ixapi.authenticate()
```

The first argument the `.api()` method takes is the IX-API URL. The second and
third arguments are the API key and secret used for authentication.

Authenticating will generate a pair of access and refresh tokens that can be
passed as argument to the `.api()` method.


## Queries

The pyixapi API is setup so that IX-API's endpoints are attributes of the
`.api()` object. Each endpoint has a handful of methods available to carry out
actions on the endpoint. For example, in order to query all the objects in the
`network-service-configs` endpoint you would do the following:

```python
>>> nsc = ixapi.network_service_configs.all()
>>> for i in nsc:
...     print(i)
...
DXDB:PAS:00001
DXDB:PAS:00002
DXDB:PAS:00003
DXDB:PAS:00004
DXDB:PAS:00005
DXDB:PAS:00006
DXDB:PAS:00007
DXDB:PAS:00008
>>>
```

Write queries are not implemented yet.
