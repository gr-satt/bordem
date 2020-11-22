from requests import Request
from requests_cache.core import CachedSession
from time import time
from os import path
import re
import json
import tempfile
import hmac
from urllib.parse import urlparse
from hashlib import sha256


import config


class BitMEX:
    '''BitMEX REST API v1 wrapper'''

    BASE_URL = 'https://www.bitmex.com/api/v1'
    if config.test:
        BASE_URL = 'https://testnet.bitmex.com/api/v1'

    _ENDPOINTS = {
            'trade_bucketed_GET': '/trade/bucketed',
            'user_wallet_GET': '/user/wallet',
            'position_GET': '/position',
            'instrument_GET': '/instrument',
            'order_POST': '/order',
            'order_bulk_POST': '/order/bulk',
            'order_all_DELETE': '/order/all'
    }

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None

        # create functions
        for func_name in self._ENDPOINTS.keys():
            endpoint = self._ENDPOINTS[func_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(func_name)
            for match in matches:
                verb = match[0]
            self._create_func(func_name, endpoint, verb)

    def _create_func(self, func_name, endpoint, verb):
        def _endpoint_request(self, **kwargs):
            response = self._request(endpoint, verb, params=kwargs)
            return response
        setattr(self.__class__, func_name, _endpoint_request)
    
    def _request(self, endpoint, verb, params):
        # create session
        if not self.session:
            cache_filename = "bitmex_cache"
            filename = path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"Accept": "application/json"})

        # prep request
        url = self.BASE_URL + endpoint
        request_ = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(request_)
        if self.api_key:
            self._set_auth_headers(prepped)

        # send request
        response_object = self.session.send(prepped)
        response = self._handle_response(response_object)
        return response

    # set auth headers on a prepped request
    def _set_auth_headers(self, prepped):
        verb = prepped.method
        parsed_url = urlparse(prepped.url)
        path = parsed_url.path
        path = "?".join([path, parsed_url.query]) if parsed_url.query else path
        expires = int(time() + 5)
        data = prepped.body or ""

        message = verb + path + str(expires) + data
        signature = hmac.new(
            key=self.api_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha256
        ).hexdigest()

        prepped.headers.update({"api-key": self.api_key})
        prepped.headers.update({"api-expires": str(expires)})
        prepped.headers.update({"api-signature": str(signature)})

    # handle repsonse / error
    def _handle_response(self, response_object):
        response = None
        try:
            response = json.loads(response_object.text)
            ratelimit = {"ratelimit": {
                "limit": response_object.headers["x-ratelimit-limit"],
                "remaining": response_object.headers["x-ratelimit-remaining"],
                "reset": response_object.headers["x-ratelimit-reset"]
            }}

            response = [dict(item) for item in response]
            response.append(ratelimit)
        
        except Exception as e:
            return e
        
        return response
