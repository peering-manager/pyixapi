from pkg_resources import DistributionNotFound, get_distribution

from pyixapi.core.api import API as api
from pyixapi.core.query import ContentError, RequestError

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass

__all__ = ("api", "ContentError", "RequestError")
