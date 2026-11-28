"""A quick test that the language model works.

Run it from the backend folder:

    python -m app.llm.check

It asks the model two easy questions and prints the answer and how long it took.
Use it after you change LLM_PROVIDER or the model in .env.
"""

import time

from pydantic import BaseModel

from app.llm import provider


class CheckAnswer(BaseModel):
    capital_of_france: str
    two_plus_three: int


def main():
    print("Using model:", provider.model_name())
    started = time.time()

    try:
        answer = provider.ask_structured(
            CheckAnswer,
            "You answer short questions. Reply only with the requested fields.",
            "What is the capital of France? What is 2 + 3?",
        )
    except provider.LLMError as error:
        print("FAILED:", error)
        return

    seconds = round(time.time() - started, 1)
    print("Answer:", answer)
    print("Took", seconds, "seconds")
    if answer.capital_of_france.strip().lower() == "paris" and answer.two_plus_three == 5:
        print("The model works.")
    else:
        print("The model answered, but the answers are wrong. Try a bigger model.")


if __name__ == "__main__":
    main()
