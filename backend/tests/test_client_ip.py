"""Forwarding headers are believed only from our own proxies.

Production: uvicorn listens on 0.0.0.0:8000 and the host firewall is open, so a
client can skip nginx/Cloudflare and send any CF-Connecting-IP — before this,
every login attempt could claim a new IP and dodge the per-IP limit."""

import importlib
import unittest

from starlette.requests import Request

from app.core.client_ip import client_ip


def _request(peer, headers=None):
    scope = {"type": "http", "method": "GET", "path": "/", "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
             "client": (peer, 50000) if peer else None}
    return Request(scope)


class TestClientIp(unittest.TestCase):
    def test_direct_client_cannot_spoof_its_ip(self):
        spoof = {"CF-Connecting-IP": "1.2.3.4", "X-Real-IP": "5.6.7.8", "X-Forwarded-For": "9.9.9.9"}
        self.assertEqual(client_ip(_request("203.0.113.7", spoof)), "203.0.113.7")

    def test_behind_nginx_cloudflare_header_wins(self):
        headers = {"CF-Connecting-IP": "198.51.100.1", "X-Real-IP": "172.68.1.1", "X-Forwarded-For": "6.6.6.6, 198.51.100.1, 172.68.1.1"}
        self.assertEqual(client_ip(_request("127.0.0.1", headers)), "198.51.100.1")

    def test_behind_nginx_without_cloudflare_uses_real_ip(self):
        self.assertEqual(client_ip(_request("127.0.0.1", {"X-Real-IP": "198.51.100.2"})), "198.51.100.2")
        self.assertEqual(client_ip(_request("::1", {"X-Real-IP": "198.51.100.2"})), "198.51.100.2")

    def test_forwarded_for_uses_the_hop_our_proxy_added(self):
        # the first hops are whatever the client typed
        self.assertEqual(client_ip(_request("127.0.0.1", {"X-Forwarded-For": "6.6.6.6, 198.51.100.3"})), "198.51.100.3")

    def test_without_headers_or_peer(self):
        self.assertEqual(client_ip(_request("127.0.0.1")), "127.0.0.1")
        self.assertIsNone(client_ip(_request(None)))

    def test_routers_use_the_shared_helper(self):
        auth_router = importlib.import_module("app.api.auth.router")
        groups_router = importlib.import_module("app.api.study_groups.router")

        spoof = _request("203.0.113.9", {"CF-Connecting-IP": "1.1.1.1"})
        self.assertEqual(auth_router._client_ip(spoof), "203.0.113.9")
        self.assertEqual(groups_router._ip(spoof), "203.0.113.9")

    def test_advertisement_click_hash_ignores_spoofed_forwarded_for(self):
        ads_router = importlib.import_module("app.api.advertisements.router")

        a = ads_router._client(_request("203.0.113.9", {"X-Forwarded-For": "1.1.1.1", "User-Agent": "UA"}))
        b = ads_router._client(_request("203.0.113.9", {"X-Forwarded-For": "2.2.2.2", "User-Agent": "UA"}))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
