from tools import codex_auto_compact_trigger_probe as trigger_probe
from tools import codex_large_context_acceptance as base
from tools import codex_remote_compaction_trigger_probe as remote_probe


def test_remote_probe_switches_shared_scanner_to_v2_markers():
    old_route = base.COMPACT_ROUTE_MARKER
    old_success = base.COMPACT_SUCCESS_MARKER
    try:
        remote_probe.configure_remote_v2_markers()
        assert base.COMPACT_ROUTE_MARKER == remote_probe.REMOTE_V2_ROUTE_MARKER
        assert base.COMPACT_SUCCESS_MARKER == remote_probe.REMOTE_V2_SUCCESS_MARKER
        assert "/v1/responses/compact" not in base.COMPACT_ROUTE_MARKER
        # The delegated trigger probe imports the same base module object.
        assert trigger_probe.base is base
    finally:
        base.COMPACT_ROUTE_MARKER = old_route
        base.COMPACT_SUCCESS_MARKER = old_success


def test_remote_success_marker_is_stricter_than_route_marker():
    assert remote_probe.REMOTE_V2_SUCCESS_MARKER.startswith(
        remote_probe.REMOTE_V2_ROUTE_MARKER
    )
    assert "completed remote compact" in remote_probe.REMOTE_V2_SUCCESS_MARKER
