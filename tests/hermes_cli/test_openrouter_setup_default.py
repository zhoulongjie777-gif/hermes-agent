"""OpenRouter setup should not select an expensive first row when the current model is absent."""

import pytest


@pytest.mark.parametrize(("current", "expected"), [
    ("missing/model", "vendor/recommended"),
    ("vendor/expensive", "vendor/expensive"),
])
def test_openrouter_setup_selects_current_or_recommended(monkeypatch, current, expected):
    from hermes_cli import auth_model_picker, model_setup_flows, models, models_pricing

    ids = ["vendor/expensive", "vendor/recommended"]
    monkeypatch.setattr(model_setup_flows, "_ensure_flow_api_key", lambda *_args, **_kw: (None, "test", False))
    monkeypatch.setattr(models, "model_ids", lambda **_kw: ids)
    monkeypatch.setattr(models, "get_preferred_silent_default_model", lambda _provider: "vendor/recommended")
    monkeypatch.setattr(models_pricing, "get_pricing_for_provider", lambda *_args, **_kw: {
        "vendor/recommended": {"prompt": "0.000001", "completion": "0.000002"},
    })
    monkeypatch.setattr(auth_model_picker, "_confirm_selection_guards", lambda *_a, **_kw: True)
    seen = {}

    def choose(_title, choices, *, selected, **_kwargs):
        seen["choices"] = choices
        return selected

    monkeypatch.setattr("hermes_cli.curses_ui.curses_radiolist", choose)
    monkeypatch.setattr(model_setup_flows, "_finish_model", lambda selected, *_a, **_kw: seen.update(selected=selected))
    model_setup_flows._model_flow_openrouter({}, current_model=current)

    assert seen["selected"] == expected
    if current not in ids:
        recommended = next(row for row in seen["choices"] if isinstance(row, list) and
                           any("vendor/recommended" in text for text, _ in row))
        assert "recommended" in "".join(text for text, _ in recommended)
        assert any("1.00" in text or "2.00" in text for text, _ in recommended)
