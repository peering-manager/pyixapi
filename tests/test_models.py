import unittest

from pyixapi.models import (
    IP,
    MAC,
    Account,
    AvailabilityZone,
    Connection,
    Contact,
    Demarc,
    Device,
    Facility,
    MemberJoiningRule,
    MetroArea,
    MetroAreaNetwork,
    NetworkFeature,
    NetworkFeatureConfig,
    NetworkService,
    NetworkServiceConfig,
    PoP,
    Port,
    PortReservation,
    ProductOffering,
    Role,
    RoleAssignment,
    RoutingFunction,
)

from .util import Response, mock_api, mock_endpoint

# Models whose __str__ is a simple field projection; Contact/IP/MAC have real
# logic and get dedicated tests below.
STR_CASES = [
    (Account, {"id": "ACCT-001", "name": "Test Account"}, "ACCT-001: Test Account"),
    (Connection, {"id": "CONN-001", "name": "Test Connection"}, "CONN-001: Test Connection"),
    (Demarc, {"id": "DEM-001"}, "DEM-001"),
    (Device, {"id": "DEV-001", "name": "Router01"}, "Router01"),
    (Facility, {"id": "FAC-001", "name": "Data Center 1"}, "Data Center 1"),
    (NetworkFeatureConfig, {"id": "NFC-001"}, "NFC-001"),
    (NetworkFeature, {"id": "NF-001"}, "NF-001"),
    (NetworkServiceConfig, {"id": "NSC-001"}, "NSC-001"),
    (NetworkService, {"id": "NS-001"}, "NS-001"),
    (PoP, {"id": "POP-001", "name": "PoP London"}, "PoP London"),
    (ProductOffering, {"id": "PROD-001", "name": "Premium Service"}, "Premium Service"),
    (MemberJoiningRule, {"id": "RULE-001"}, "RULE-001"),
    (MetroArea, {"id": "METRO-001", "display_name": "New York Metro"}, "New York Metro"),
    (MetroAreaNetwork, {"id": "MAN-001", "name": "NYC Network"}, "NYC Network"),
    (Port, {"id": "PORT-001", "name": "eth0"}, "eth0"),
    (PortReservation, {"id": "RES-001"}, "RES-001"),
    (Role, {"id": "ROLE-001", "name": "Administrator"}, "Administrator"),
    (AvailabilityZone, {"id": "AZ-001", "name": "Zone A"}, "Zone A"),
    (RoutingFunction, {"id": "RF-001"}, "RF-001"),
    (RoleAssignment, {"id": "ASSIGN-001"}, "ASSIGN-001"),
]


class ModelStrTestCase(unittest.TestCase):
    def test_str(self) -> None:
        for model, values, expected in STR_CASES:
            with self.subTest(model=model.__name__):
                obj = model(values, mock_api(), mock_endpoint())
                self.assertEqual(str(obj), expected)


class ContactStrTestCase(unittest.TestCase):
    """Contact.__str__ joins the populated fields and falls back to id."""

    def test_all_fields(self) -> None:
        contact = Contact(
            {"id": "CONT-001", "legal_company_name": "Acme Corp", "name": "John Doe", "email": "john@example.com"},
            mock_api(),
            mock_endpoint(),
        )
        self.assertEqual(str(contact), "Acme Corp - John Doe - john@example.com")

    def test_partial_fields(self) -> None:
        contact = Contact(
            {"id": "CONT-001", "name": "John Doe", "email": "john@example.com"}, mock_api(), mock_endpoint()
        )
        self.assertEqual(str(contact), "John Doe - john@example.com")

    def test_fallback_to_id(self) -> None:
        contact = Contact({"id": "CONT-001"}, mock_api(), mock_endpoint())
        self.assertEqual(str(contact), "CONT-001")


class IPTestCase(unittest.TestCase):
    """IP exposes ipaddress-derived cidr/ip/network properties."""

    def test_ipv4(self) -> None:
        ip = IP({"address": "192.0.2.1", "prefix_length": 24}, mock_api(), mock_endpoint())
        self.assertEqual(str(ip.cidr), "192.0.2.1/24")
        self.assertEqual(str(ip.ip), "192.0.2.1")
        self.assertEqual(str(ip.network), "192.0.2.0/24")
        self.assertEqual(str(ip), "192.0.2.1/24")

    def test_ipv6(self) -> None:
        ip = IP({"address": "2001:db8::1", "prefix_length": 64}, mock_api(), mock_endpoint())
        self.assertEqual(str(ip.cidr), "2001:db8::1/64")
        self.assertEqual(str(ip.ip), "2001:db8::1")
        self.assertEqual(str(ip.network), "2001:db8::/64")
        self.assertEqual(str(ip), "2001:db8::1/64")


class MACTestCase(unittest.TestCase):
    def test_str_is_lowercased(self) -> None:
        mac = MAC({"address": "00:11:22:AA:BB:CC"}, mock_api(), mock_endpoint())
        self.assertEqual(str(mac), "00:11:22:aa:bb:cc")


class SubResourceTestCase(unittest.TestCase):
    """
    Base class for sub-resource action tests.

    The meaningful behavior of these methods is the URL and HTTP verb they
    derive from the record id and sub-path; the response body is plumbed
    straight through by Request, so we assert the call, not the echo.
    """

    def setUp(self) -> None:
        self.api = mock_api()

    def assert_called(self, method: str, suffix: str) -> None:
        mock = getattr(self.api.http_session, method)
        mock.assert_called_once()
        url = mock.call_args[0][0]
        self.assertTrue(url.endswith(suffix), f"{url!r} does not end with {suffix!r}")

    def params(self, method: str) -> dict:
        return getattr(self.api.http_session, method).call_args[1]["params"]


class ConnectionSubResourceTestCase(SubResourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.endpoint = mock_endpoint(name="connections", url="https://api.example.net/v2/connections")
        self.conn = Connection({"id": "CONN-001", "name": "C"}, self.api, self.endpoint)

    def test_cancellation_policy(self) -> None:
        self.conn.cancellation_policy()
        self.assert_called("get", "/connections/CONN-001/cancellation-policy")

    def test_get_loa(self) -> None:
        self.conn.get_loa()
        self.assert_called("get", "/connections/CONN-001/loa")

    def test_upload_loa_posts(self) -> None:
        self.conn.upload_loa({"file": "base64data"})
        self.assert_called("post", "/connections/CONN-001/loa")

    def test_statistics(self) -> None:
        self.conn.statistics()
        self.assert_called("get", "/connections/CONN-001/statistics")

    def test_statistics_forwards_kwargs_as_params(self) -> None:
        self.conn.statistics(from_date="2024-01-01", to_date="2024-12-31")
        self.assertEqual(self.params("get"), {"from_date": "2024-01-01", "to_date": "2024-12-31"})

    def test_statistics_timeseries_builds_aggregate_path(self) -> None:
        self.conn.statistics_timeseries("5m", from_date="2024-01-01")
        self.assert_called("get", "/connections/CONN-001/statistics/5m/timeseries")
        self.assertEqual(self.params("get"), {"from_date": "2024-01-01"})


class NetworkServiceSubResourceTestCase(SubResourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.endpoint = mock_endpoint(name="network-services", url="https://api.example.net/v2/network-services")
        self.ns = NetworkService({"id": "NS-001"}, self.api, self.endpoint)

    def test_cancellation_policy(self) -> None:
        self.ns.cancellation_policy()
        self.assert_called("get", "/network-services/NS-001/cancellation-policy")

    def test_change_request_get(self) -> None:
        self.ns.change_request()
        self.assert_called("get", "/network-services/NS-001/change-request")

    def test_create_change_request_posts(self) -> None:
        self.ns.create_change_request({"capacity": 1000})
        self.assert_called("post", "/network-services/NS-001/change-request")

    def test_delete_change_request_deletes(self) -> None:
        self.api.http_session.delete.return_value = Response(content=None)
        result = self.ns.delete_change_request()
        self.assert_called("delete", "/network-services/NS-001/change-request")
        self.assertTrue(result)

    def test_rtt_statistics(self) -> None:
        self.ns.rtt_statistics()
        self.assert_called("get", "/network-services/NS-001/rtt-statistics")

    def test_statistics(self) -> None:
        self.ns.statistics()
        self.assert_called("get", "/network-services/NS-001/statistics")

    def test_statistics_timeseries_builds_aggregate_path(self) -> None:
        self.ns.statistics_timeseries("1h")
        self.assert_called("get", "/network-services/NS-001/statistics/1h/timeseries")


class NetworkServiceConfigSubResourceTestCase(SubResourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.endpoint = mock_endpoint(
            name="network-service-configs", url="https://api.example.net/v2/network-service-configs"
        )
        self.nsc = NetworkServiceConfig({"id": "NSC-001"}, self.api, self.endpoint)

    def test_cancellation_policy(self) -> None:
        self.nsc.cancellation_policy()
        self.assert_called("get", "/network-service-configs/NSC-001/cancellation-policy")

    def test_peer_statistics(self) -> None:
        self.nsc.peer_statistics()
        self.assert_called("get", "/network-service-configs/NSC-001/peer-statistics")

    def test_peer_statistics_timeseries_builds_aggregate_path(self) -> None:
        self.nsc.peer_statistics_timeseries("5m")
        self.assert_called("get", "/network-service-configs/NSC-001/peer-statistics/5m/timeseries")

    def test_statistics(self) -> None:
        self.nsc.statistics()
        self.assert_called("get", "/network-service-configs/NSC-001/statistics")

    def test_statistics_timeseries_builds_aggregate_path(self) -> None:
        self.nsc.statistics_timeseries("5m")
        self.assert_called("get", "/network-service-configs/NSC-001/statistics/5m/timeseries")


class PortSubResourceTestCase(SubResourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.endpoint = mock_endpoint(name="ports", url="https://api.example.net/v2/ports")
        self.port = Port({"id": "PORT-001", "name": "eth0"}, self.api, self.endpoint)

    def test_statistics(self) -> None:
        self.port.statistics()
        self.assert_called("get", "/ports/PORT-001/statistics")

    def test_statistics_timeseries_builds_aggregate_path(self) -> None:
        self.port.statistics_timeseries("5m")
        self.assert_called("get", "/ports/PORT-001/statistics/5m/timeseries")


class PortReservationSubResourceTestCase(SubResourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.endpoint = mock_endpoint(name="port-reservations", url="https://api.example.net/v2/port-reservations")
        self.pr = PortReservation({"id": "RES-001"}, self.api, self.endpoint)

    def test_cancellation_policy(self) -> None:
        self.pr.cancellation_policy()
        self.assert_called("get", "/port-reservations/RES-001/cancellation-policy")

    def test_get_loa(self) -> None:
        self.pr.get_loa()
        self.assert_called("get", "/port-reservations/RES-001/loa")

    def test_upload_loa_posts(self) -> None:
        self.pr.upload_loa({"file": "base64data"})
        self.assert_called("post", "/port-reservations/RES-001/loa")


class RoutingFunctionSubResourceTestCase(SubResourceTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.endpoint = mock_endpoint(name="routing-functions", url="https://api.example.net/v2/routing-functions")
        self.rf = RoutingFunction({"id": "RF-001"}, self.api, self.endpoint)

    def test_cancellation_policy(self) -> None:
        self.rf.cancellation_policy()
        self.assert_called("get", "/routing-functions/RF-001/cancellation-policy")
