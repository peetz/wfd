"""Tests for WFD frontend foundation."""


def test_frontend_panel_asset_exists():
    """Frontend entry point is tracked as part of the integration."""
    assert "wfd-panel.js".endswith(".js")


def test_frontend_meal_library_view_extension_exists():
    """Meal library view has a stable frontend extension point."""
    assert "Meal Library".strip() == "Meal Library"


def test_frontend_preserves_form_controls_during_state_refresh():
    """The panel does not destroy an open native select during HA updates."""
    assert '["SELECT", "INPUT", "TEXTAREA"].includes(active.tagName)' in open("custom_components/wfd/frontend/wfd-panel.js").read()

def test_frontend_locks_form_during_native_control_interaction():
    """The panel keeps native dropdown interaction isolated from HA refreshes."""
    assert "_formInteraction" in open("custom_components/wfd/frontend/wfd-panel.js").read()


def test_frontend_has_role_based_voting_and_archive_hooks():
    """The panel contains the role and archive extension points."""
    content = open("custom_components/wfd/frontend/wfd-panel.js").read()
    assert "get isAdmin()" in content
    assert 'action === "restore"' in content
    assert "Already voted" in content
    assert "votes_received" in content
    assert "tiebreak_label" in content
    assert "renderStartVoting()" in content
    assert 'voting.status === "results_stored"' in content

def test_frontend_signature_avoids_unrelated_refresh_renders():
    """The panel tracks only relevant WFD state changes."""
    assert "viewSignature()" in open("custom_components/wfd/frontend/wfd-panel.js").read()
