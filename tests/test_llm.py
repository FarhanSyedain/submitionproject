"""LLM service layer: parser, router, mock client."""
import pytest

from services.llm.base import parse_json
from services.llm.mock_client import MockClient
from services.llm.router import get_llm_client


class TestParseJson:
    def test_raw_json(self):
        assert parse_json('{"a": 1}') == {"a": 1}

    def test_with_code_fence(self):
        text = '```json\n{"a": 1, "b": [2, 3]}\n```'
        assert parse_json(text) == {"a": 1, "b": [2, 3]}

    def test_with_preamble(self):
        text = 'Here you go:\n{"verdict": "yes"}\nThanks!'
        assert parse_json(text) == {"verdict": "yes"}

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_json("")

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            parse_json("not json at all")


class TestRouter:
    def test_default_returns_mock(self, settings):
        settings.LLM_PROVIDER = "mock"
        client = get_llm_client()
        assert client.provider == "mock"

    def test_explicit_override(self, settings):
        settings.LLM_PROVIDER = "ollama"
        client = get_llm_client("mock")
        assert client.provider == "mock"

    def test_unknown_provider_falls_back_to_mock(self, settings):
        settings.LLM_PROVIDER = "unknown"
        client = get_llm_client()
        assert client.provider == "mock"


class TestMockClient:
    def test_returns_canned_data_per_module(self, mock_client):
        data, result = mock_client.complete_json(
            system="x", user="y", module="competitor"
        )
        assert "competitors" in data
        assert len(data["competitors"]) >= 1
        assert result.completion_tokens > 0

    def test_unknown_module_returns_empty_dict(self, mock_client):
        data, _ = mock_client.complete_json(
            system="x", user="y", module="nonexistent"
        )
        assert data == {}
