"""The one place that talks to a language model (an LLM).

The rest of the app calls ask_structured() and never knows whether the answer came
from Ollama on your own machine or from OpenAI. The choice is the LLM_PROVIDER
setting in .env, so switching is a one-line change.
"""

from app.core.config import settings


class LLMError(Exception):
    """The language model cannot be used, or gave no usable answer."""

    pass


def get_chat_model():
    """Build the chat model chosen in the settings."""
    provider = settings.llm_provider.strip().lower()

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise LLMError("The package langchain-ollama is not installed. Run: pip install langchain-ollama")
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            client_kwargs={"timeout": settings.llm_timeout_seconds},
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMError("LLM_PROVIDER is openai, but OPENAI_API_KEY is empty.")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise LLMError("The package langchain-openai is not installed. Run: pip install langchain-openai")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
        )

    raise LLMError("Unknown LLM_PROVIDER '" + settings.llm_provider + "'. Use 'ollama' or 'openai'.")


def model_name():
    """A short name of the model in use, like "ollama:qwen2.5:7b". We store it with each report."""
    provider = settings.llm_provider.strip().lower()
    if provider == "openai":
        return "openai:" + settings.openai_model
    return provider + ":" + settings.ollama_model


def ask_structured(schema, system_prompt, user_prompt, model=None):
    """Ask the model a question and get the answer back as a filled-in `schema`.

    schema is a Pydantic class that describes the answer we want, for example one
    with the fields "verdict" and "reason". The model must fill those in, and anything
    that does not fit the shape is rejected. Small models sometimes get it wrong,
    so we try again a couple of times before giving up.

    model is only passed in by tests, to use a fake model.
    """
    if model is None:
        model = get_chat_model()

    structured_model = model.with_structured_output(schema)
    messages = [("system", system_prompt), ("human", user_prompt)]

    tries = settings.llm_max_retries + 1
    last_problem = "no answer"

    for _ in range(tries):
        try:
            answer = structured_model.invoke(messages)
        except Exception as error:  # a connection problem, bad JSON, or an answer that does not fit
            last_problem = str(error)
            continue

        if isinstance(answer, schema):
            return answer
        last_problem = "the model returned an empty or wrong answer"

    raise LLMError(
        "The model (" + model_name() + ") gave no usable answer after "
        + str(tries) + " tries. Last problem: " + last_problem
    )
