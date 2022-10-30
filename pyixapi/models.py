import ipaddress

from pyixapi.core.response import Record

# Version 1 and up


class Account(Record):
    """
    An Account represents an account that holds objects in IX-API.

    It is also referenced as "customer" in IX-API v1.
    """

    def __str__(self):
        return f"{self.id}: {self.name}"


class Connection(Record):
    """
    A Connection is a group of physical ports collected together into a LAG.
    """

    def __str__(self):
        return f"{self.id}: {self.name}"


class Contact(Record):
    """
    A Contact is a role undertaking a specific responsibility within an account.
    """

    def __str__(self):
        r = []

        legal_company_name = getattr(self, "legal_company_name", None)
        if legal_company_name is not None:
            r.append(legal_company_name)
        name = getattr(self, "name", None)
        if name is not None:
            r.append(name)
        email = getattr(self, "email", None)
        if email is not None:
            r.append(email)
        return " - ".join(r) or self.id


class Demarc(Record):
    """
    A Demarc (demarcation point) is the point at which customer and IXP networks meet,
    eg a physical port / socket, generally with a specified bandwidth.
    """

    def __str__(self):
        return self.id


class Device(Record):
    """
    A Device is a network hardware device, typically a switch, which is located at a
    specified facility and inside a PoP.
    """

    def __str__(self):
        return self.name


class Facility(Record):
    """
    A Facility is a data centre, with a determined physical address, from which a
    defined set of PoPs can be accessed.
    """

    def __str__(self):
        return self.name


class IP(Record):
    """
    An IP is an IPv4 or IPv6 address, with a given validity period.
    """

    @property
    def cidr(self):
        return ipaddress.ip_interface(f"{self.address}/{self.prefix_length}")

    @property
    def ip(self):
        return self.cidr.ip

    @property
    def network(self):
        return self.cidr.network

    def __str__(self):
        return str(self.cidr)


class MAC(Record):
    """
    A MAC is a MAC address with a given validity period.
    """

    def __str__(self):
        return self.address.lower()


class NetworkFeatureConfig(Record):
    """
    A NetworkFeatureConfig is a customer's configuration to use a NetworkFeature.
    """

    def __str__(self):
        return self.id


class NetworkFeature(Record):
    """
    A NetworkFeature is a functionality made available to customers within a
    NetworkService.
    """

    def __str__(self):
        return self.id


class NetworkServiceConfig(Record):
    """
    A NetworkServiceConfig is a customer's configuration to use a NetworkService, eg
    the configuration of a (subset of a) connection for that customer's traffic.
    """

    def __str__(self):
        return self.id


class NetworkService(Record):
    """
    A NetworkService is an instances of a Product accessible by one or multiple users,
    depending on the type of product.
    """

    def __str__(self):
        return self.id


class PoP(Record):
    """
    A PoP is a location within a Facility which is connected to a single network
    infrastructure and has defined reachability of other facilities.
    """

    def __str__(self):
        return self.name


class Product(Record):
    """
    A Product is a network or peering-related product of a defined type sold by an IXP
    to its customers.
    """

    def __str__(self):
        return self.name


# Version 2 and up


class MemberJoiningRule(Record):
    """
    A MemberJoiningRule defines a rule to allow or deny access for an Account to a
    access a NetworkService.

    Furthermore, some NetworkServices may only be visible if the querying account is
    listed in an allow rule.
    """

    def __str__(self):
        return self.id


class MetroArea(Record):
    """
    A MetroArea exists if a MetroAreaNetwork or Facility is present in it.
    """

    def __str__(self):
        return self.display_name


class MetroAreaNetwork(Record):
    """
    Services are provided directly on or can be consumed from inside a
    MetroAreaNetwork.

    Accounts can indicate their presence in a MetroAreaNetwork to others by adding a
    list of IDs.
    """

    def __str__(self):
        return self.name


class Port(Record):
    """
    A Port is the point at which subscriber and IXP networks meet. A port is always
    associated with a device and pop, has a speed and a media_type.
    """

    def __str__(self):
        return self.name


class PortReservation(Record):
    """
    A PortReservation expresses the intent to include a Port in a connection.

    Decommissining a port-reservation will lead to the removal of the port from the
    LAG.

    Please note that individual cancellation policies might apply.
    """

    def __str__(self):
        return self.id


class ProductOffering(Record):
    """
    A ProductOffering is an offer made by an exchange to be consumed by a client.
    """

    def __str__(self):
        return self.name


class Role(Record):
    """
    A Role enables a Contact to act for a specific purpose.
    """

    def __str__(self):
        return self.name


class RoleAssignment(Record):
    """
    A Contact can be assigned to many Roles.
    """

    def __str__(self):
        return self.id
