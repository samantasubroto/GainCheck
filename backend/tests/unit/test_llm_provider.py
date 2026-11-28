import pytest
from pydantic import BaseModel

from app.core.config import settings
from app.llm import provider


class Answer(BaseModel):
    verdict: str
    reason: str


# ---------- a fake model, so no real LLM is needed ----------


class FakeStructuredModel:
    """Gives the answers we list, one per call. An item that is an Exception is raised instead."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeModel:
    def __init__(self, results):
        self.structured = FakeStructuredModel(results)
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured


GOOD = Answer(verdict="plateau", reason="no change")


# ---------- ask_structured ----------


def test_a_good_answer_is_returned(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_retries", 2)
    model = FakeModel([GOOD])

    answer = provider.ask_structured(Answer, "system", "user", model=model)

    assert answer == GOOD
    assert model.schema is Answer
    assert model.structured.calls == 1


def test_it_tries_again_after_a_bad_answer(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_retries", 2)
    model = FakeModel([ValueError("not valid JSON"), None, GOOD])

    answer = provider.ask_structured(Answer, "system", "user", model=model)

    assert answer == GOOD
    assert model.structured.calls == 3


def test_it_gives_up_after_all_tries_and_says_why(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_retries", 1)
    model = FakeModel([ValueError("first problem"), ConnectionError("connection refused")])

    with pytest.raises(provider.LLMError) as error:
        provider.ask_structured(Answer, "system", "user", model=model)

    assert model.structured.calls == 2
    assert "connection refused" in str(error.value)


def test_a_wrong_kind_of_answer_counts_as_a_failure(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_retries", 0)
    model = FakeModel([{"verdict": "plateau"}])  # a dictionary, not an Answer

    with pytest.raises(provider.LLMError):
        provider.ask_structured(Answer, "system", "user", model=model)


# ---------- choosing the provider ----------


def test_an_unknown_provider_is_an_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "banana")
    with pytest.raises(provider.LLMError) as error:
        provider.get_chat_model()
    assert "banana" in str(error.value)


def test_openai_without_a_key_is_an_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(provider.LLMError) as error:
        provider.get_chat_model()
    assert "OPENAI_API_KEY" in str(error.value)


def test_provider_name_is_not_case_sensitive(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "  OpenAI ")
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(provider.LLMError) as error:
        provider.get_chat_model()
    assert "OPENAI_API_KEY" in str(error.value)  # it was understood as openai


# ---------- model name ----------


def test_model_name_for_ollama(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "qwen2.5:7b")
    assert provider.model_name() == "ollama:qwen2.5:7b"


def test_model_name_for_openai(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_model", "gpt-4o-mini")
    assert provider.model_name() == "openai:gpt-4o-mini"
