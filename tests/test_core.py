"""Tests for the core layer (no GUI required)."""

import time
import pytest

from cloudflare_warp.core.warp_service import WarpService, WarpStatus
from cloudflare_warp.core.config import Config


# ---------------------------------------------------------------------------
# WarpService tests
# ---------------------------------------------------------------------------

class TestWarpService:
    def setup_method(self):
        self.svc = WarpService()

    def test_initial_status_disconnected(self):
        assert self.svc.status == WarpStatus.DISCONNECTED

    def test_is_not_real_client_in_test_env(self):
        # warp-cli won't be present in CI
        assert self.svc.is_real_client is False

    def test_connect_transitions_through_connecting(self):
        states = []
        self.svc.add_status_callback(states.append)
        self.svc.connect()
        time.sleep(0.1)
        assert WarpStatus.CONNECTING in states

    def test_connect_reaches_connected(self):
        states = []
        self.svc.add_status_callback(states.append)
        self.svc.connect()
        # Give simulated connect time to finish
        time.sleep(3)
        assert WarpStatus.CONNECTED in states

    def test_disconnect_after_connect(self):
        self.svc.connect()
        time.sleep(3)
        assert self.svc.status == WarpStatus.CONNECTED

        states = []
        self.svc.add_status_callback(states.append)
        self.svc.disconnect()
        time.sleep(2)
        assert WarpStatus.DISCONNECTED in states

    def test_connection_info_populated_when_connected(self):
        self.svc.connect()
        time.sleep(3)
        info = self.svc.connection_info
        assert info["ip"] != ""
        assert info["city"] != ""

    def test_add_remove_callback(self):
        calls = []
        cb = calls.append
        self.svc.add_status_callback(cb)
        self.svc.connect()
        time.sleep(0.1)
        self.svc.remove_status_callback(cb)
        count_after_remove = len(calls)
        self.svc.disconnect()
        time.sleep(2)
        # No new calls after removal
        assert len(calls) == count_after_remove


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestConfig:
    def setup_method(self, tmp_path=None):
        import tempfile, os
        from pathlib import Path
        import cloudflare_warp.core.config as cfg_module

        # Redirect config to a temp dir so tests don't pollute the real config
        self._old_dir = cfg_module._CONFIG_DIR
        self._old_file = cfg_module._CONFIG_FILE
        tmp = Path(tempfile.mkdtemp())
        cfg_module._CONFIG_DIR = tmp / "cfg"
        cfg_module._CONFIG_FILE = cfg_module._CONFIG_DIR / "config.json"
        self.cfg = Config()

    def teardown_method(self):
        import cloudflare_warp.core.config as cfg_module
        cfg_module._CONFIG_DIR = self._old_dir
        cfg_module._CONFIG_FILE = self._old_file

    def test_defaults(self):
        assert self.cfg.get("theme") == "dark"
        assert self.cfg.get("dns_mode") == "warp"

    def test_set_and_get(self):
        self.cfg.set("dns_mode", "doh")
        assert self.cfg.get("dns_mode") == "doh"

    def test_missing_key_returns_default(self):
        assert self.cfg.get("nonexistent", "fallback") == "fallback"

    def test_all_returns_dict(self):
        d = self.cfg.all()
        assert isinstance(d, dict)
        assert "theme" in d

    def test_persistence(self):
        import cloudflare_warp.core.config as cfg_module
        self.cfg.set("account_type", "warp_plus")
        # Re-load from the same temp file
        cfg2 = Config()
        assert cfg2.get("account_type") == "warp_plus"
