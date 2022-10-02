import requests

from pyixapi.core.endpoint import Endpoint
from pyixapi.core.query import Request
from pyixapi.core.response import Record
from pyixapi.core.token import Token
from pyixapi.core.util import cat
from pyixapi.models import (
    IP,
    MAC,
    Account,
    Connection,
    Contact,
    Demarc,
    Device,
    Facility,
    NetworkFeature,
    NetworkFeatureConfig,
    NetworkService,
    NetworkServiceConfig,
    PoP,
    Product,
)

__version__ = "0.1.1"


class API(object):
    """
    The API object is the entrypoint for pyixapi.

    After instantiating the API() with the appropriate named arguments you can specify
    which app and endpoint you wish to interact with.
    """

    def __init__(
        self,
        url,
        key,
        secret,
        access_token="",
        refresh_token="",
        user_agent=f"pyixapi/{__version__}",
    ):
        self.url = url.rstrip("/")
        self.key = key
        self.secret = secret
        self.access_token = Token.from_jwt(access_token) if access_token else None
        self.refresh_token = Token.from_jwt(refresh_token) if refresh_token else None
        self.http_session = requests.Session()
        self.user_agent = user_agent

        self.auth = Endpoint(self, "auth")
        self.connections = Endpoint(self, "connections", model=Connection)
        self.contacts = Endpoint(self, "contacts", model=Contact)
        self.customers = Endpoint(self, "customers", model=Account)
        self.demarcs = Endpoint(self, "demarcs", model=Demarc)
        self.devices = Endpoint(self, "devices", model=Device)
        self.facilities = Endpoint(self, "facilities", model=Facility)
        self.ips = Endpoint(self, "ips", model=IP)
        self.macs = Endpoint(self, "macs", model=MAC)
        self.network_feature_configs = Endpoint(
            self, "network-feature-configs", model=NetworkFeatureConfig
        )
        self.network_features = Endpoint(self, "network-features", model=NetworkFeature)
        self.network_service_configs = Endpoint(
            self, "network-service-configs", model=NetworkServiceConfig
        )
        self.network_services = Endpoint(self, "network-services", model=NetworkService)
        self.pops = Endpoint(self, "pops", model=PoP)
        self.products = Endpoint(self, "products", model=Product)

    @property
    def version(self):
        """
        Get the API version of IX-API.
        """
        return Request(
            base=self.url, token=self.access_token, http_session=self.http_session
        ).get_version()

    def authenticate(self):
        """
        Authenticate and generate a pair of tokens.
        """
        r = Request(
            cat(self.url, "auth", "token"), http_session=self.http_session
        ).post(data={"api_key": self.key, "api_secret": self.secret})

        self.access_token = Token.from_jwt(r["access_token"])
        self.refresh_token = Token.from_jwt(r["refresh_token"])

        return Record(r, self, self.auth)

    def refresh_authentication(self):
        """
        Prolong authentication by refreshing the tokens pair.
        """
        r = Request(
            cat(self.url, "auth", "refresh"),
            token=self.refresh_token.encoded,
            http_session=self.http_session,
        ).post(data={"refresh_token": self.refresh_token.encoded})

        self.access_token = Token.from_jwt(r["access_token"])
        self.refresh_token = Token.from_jwt(r["refresh_token"])

        return Record(r, self, self.auth)

    def health(self):
        """
        Get the health information from IX-API.

        Available in IX-API 2 or newer.
        """
        if self.version == 1:
            return {}

        return Request(
            base=self.url, token=self.access_token, http_session=self.http_session
        ).get_health()
