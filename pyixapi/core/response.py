from pyixapi.core.query import Request
from pyixapi.core.util import Hashabledict


def get_return(lookup):
    """
    Return simple representations for items passed to lookup.

    Used to return a "simple" representation of objects and collections sent to it via
    lookup. We check if it's a :py:class:`.Record`, if so simply return its ID.
    """
    if isinstance(lookup, Record):
        return getattr(lookup, "id")
    else:
        return lookup


class RecordSet(object):
    """
    Iterator containing :py:class:`.Record` objects.

    Returned by :py:meth:`.Endpoint.all()` and :py:meth:`.Endpoint.filter()` methods.
    Allows iteration of and actions to be taken on the results from the aforementioned
    methods.

    :Examples:

    To see how many results are in a query by calling ``len()``:

    >>> x = ixapi.network_service_configs.all()
    >>> len(x)
    23
    >>>

    Simple iteration of the results:

    >>> configs = ixapi.network_service_configs.all()
    >>> for config in configs:
    ...     print(config.id)
    ...
    DXDB:PAS:000001
    DXDB:PAS:000002
    DXDB:PAS:000003
    DXDB:PAS:000004
    DXDB:PAS:000005
    DXDB:PAS:000006
    DXDB:PAS:000007
    DXDB:PAS:000008
    DXDB:PAS:000009
    DXDB:PAS:000010
    DXDB:PAS:000011
    >>>
    """

    def __init__(self, endpoint, request, **kwargs):
        self.endpoint = endpoint
        self.request = request
        self.response = self.request.get()
        self._response_cache = []

    def __iter__(self):
        return self

    def __next__(self):
        if self._response_cache:
            return self.endpoint.return_obj(
                self._response_cache.pop(), self.endpoint.api, self.endpoint
            )
        return self.endpoint.return_obj(
            next(self.response), self.endpoint.api, self.endpoint
        )

    def __len__(self):
        try:
            return self.request.count
        except AttributeError:
            try:
                self._response_cache.append(next(self.response))
            except StopIteration:
                return 0
            return self.request.count


class Record(object):
    """
    Create Python objects from IX-API responses.

    Nested dicts that represent other endpoints are also turned into
    :py:class:`.Record` objects. All fields are then assigned to the object's
    attributes. If a missing attribute is requested (e.g. requesting a field that's
    only present on a full response on a :py:class:`.Record` made from a nested
    response) then pyixapi will make a request for the full object and return the
    requested value.

    :examples:
    Default representation of the object is usually its ID and/or name:
    >>> x = ixapi.network_service_configs.get("DXDB:PAS:000001")
    >>> x
    DXDB:PAS:000001
    >>>

    Querying a string field:
    >>> x = ixapi.network_service_configs.get("DXDB:PAS:000001")
    >>> x.type
    'exchange_lan'
    >>>

    Querying a field on a nested object:
    >>> x = nb.dcim.devices.get(1)
    >>> x.device_type.model
    'QFX5100-24Q'
    >>>

    Casting the object as a dictionary:
    >>> from pprint import pprint
    >>> pprint(dict(x))
    {'asns': [64500],
     'capacity': 2500,
     'connection': 'DXDB:NAS:000001',
     'consuming_customer': 'DXDB:CUST:0001',
     'contacts': [],
     'contract_ref': None,
     'external_ref': None,
     'id': 'DXDB:PAS:000001',
     'inner_vlan': 10,
     'ips': ['DXDB:IPV6:00001', 'DXDB:IPV4:00001'],
     'macs': ['DXDB:MAC:00001'],
     'managing_customer': 'DXDB:CUST:0001',
     'network_feature_configs': ['DXDB:RSAS:000001',
                                 'DXDB:RSAS:000002',
                                 'DXDB:RSAS:000003',
                                 'DXDB:RSAS:000004'],
     'network_service': 'DXDB:PS:00001',
     'outer_vlan': 20,
     'purchase_order': '',
     'state': 'production',
     'status': [],
     'type': 'exchange_lan'}
    >>>

    Iterating over a :py:class:`.Record` object:
    >>> for i in x:
    ...  print(i)
    ...
    ('asns', [64500])
    ('capacity', 200000)
    ('connection', 'DXDB:NAS:00001')
    >>>
    """

    url = None

    def __init__(self, values, api, endpoint):
        self._full_cache = []
        self._init_cache = []
        self.api = api
        self.default_ret = Record
        self.endpoint = endpoint
        if values:
            self._parse_values(values)

    def __iter__(self):
        for i in dict(self._init_cache):
            a = getattr(self, i)
            if isinstance(a, Record):
                yield i, dict(a)
            elif isinstance(a, list) and all(isinstance(i, Record) for i in a):
                yield i, [dict(x) for x in a]
            else:
                yield i, a

    def __getitem__(self, k):
        return dict(self)[k]

    def __str__(self):
        if hasattr(self, "id"):
            return self.id
        else:
            return str(self.endpoint)

    def __repr__(self):
        return str(dict(self))

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __key__(self):
        if hasattr(self, "id"):
            return (self.endpoint.name, self.id)
        else:
            return self.endpoint.name

    def __hash__(self):
        return hash(self.__key__())

    def __eq__(self, other):
        if isinstance(other, Record):
            return self.__key__() == other.__key__()
        return NotImplemented

    def _add_cache(self, item):
        key, value = item
        self._init_cache.append((key, get_return(value)))

    def _parse_values(self, values):
        """
        Parse values dict at init and sets object attributes with the values within.
        """

        def list_parser(key_name, list_item):
            if isinstance(list_item, dict):
                lookup = getattr(self.__class__, key_name, None)
                if not isinstance(lookup, list):
                    # This is *list_parser*, so if the custom model field is not
                    # a list (or is not defined), just return the default model
                    return self.default_ret(list_item, self.api, self.endpoint)
                else:
                    model = lookup[0]
                    return model(list_item, self.api, self.endpoint)
            return list_item

        for k, v in values.items():
            if isinstance(v, dict):
                lookup = getattr(self.__class__, k, None)
                if lookup:
                    v = lookup(v, self.api, self.endpoint)
                else:
                    v = self.default_ret(v, self.api, self.endpoint)
                self._add_cache((k, v))
            elif isinstance(v, list):
                v = [list_parser(k, i) for i in v]
                to_cache = list(v)
                self._add_cache((k, to_cache))
            else:
                self._add_cache((k, v))
            setattr(self, k, v)

    def serialize(self, nested=False, init=False):
        """
        Pull all the attributes in an object and create a dict that can be turned into
        the JSON that IX-API is expecting.

        If an attribute's value is a :py:class:`.Record` type it's replaced with the
        `id` field of that object.
        """
        if nested:
            return get_return(self)

        if init:
            init_vals = dict(self._init_cache)

        r = {}
        for i in dict(self):
            current_val = getattr(self, i) if not init else init_vals.get(i)
            if isinstance(current_val, Record):
                current_val = getattr(current_val, "serialize")(nested=True)
            if isinstance(current_val, list):
                current_val = [
                    v.id if isinstance(v, Record) else v for v in current_val
                ]
            r[i] = current_val
        return r

    def _diff(self):
        def fmt_dict(k, v):
            if isinstance(v, dict):
                return k, Hashabledict(v)
            if isinstance(v, list):
                return k, ",".join(map(str, v))
            return k, v

        current = Hashabledict({fmt_dict(k, v) for k, v in self.serialize().items()})
        init = Hashabledict(
            {fmt_dict(k, v) for k, v in self.serialize(init=True).items()}
        )
        return set([i[0] for i in set(current.items()) ^ set(init.items())])

    def updates(self):
        """
        Compile changes for an existing object into a dict.

        Take a diff between the objects current state and its state at init and return
        them as a dict, which will be empty if no changes.
        """
        if self.id:
            diff = self._diff()
            if diff:
                serialized = self.serialize()
                return {i: serialized[i] for i in diff}
        return {}

    def save(self):
        """
        Save changes to an existing object.

        Take a diff between the objects current state and its state at init and sends
        them as a dict to :py:meth:`Request.patch()`.
        """
        updates = self.updates()
        if updates:
            r = Request(
                key=self.id,
                base=self.endpoint.url,
                token=self.api.token,
                http_session=self.api.http_session,
            )
            if r.patch(updates):
                return True
        return False

    def update(self, data):
        """
        Update an object with a dictionary.

        Accept a dict and use it to update the record and call
        :py:meth:`Request.save()`.
        """

        for k, v in data.items():
            setattr(self, k, v)
        return self.save()

    def delete(self):
        """
        Delete an existing object.
        """
        r = Request(
            key=self.id,
            base=self.endpoint.url,
            token=self.api.token,
            http_session=self.api.http_session,
        )
        return True if r.delete() else False
