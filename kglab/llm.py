"""One function, `complete`, that sends a conversation to Claude or to OpenAI.

The few-shot examples are ordinary earlier turns of the conversation: a user
turn with an example file, then an assistant turn with the JSON we want back.
Each provider is called through its own official SDK.
"""
import os
import sys

from kglab import settings

KEY_NAMES = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}


def check_ready() -> None:
    """Stop early, with a clear message, if the provider or its key is missing."""
    key = KEY_NAMES.get(settings.LLM_PROVIDER)
    if key is None:
        sys.exit(f"LLM_PROVIDER must be 'anthropic' or 'openai', not {settings.LLM_PROVIDER!r}")
    if not os.getenv(key) and not (key == "ANTHROPIC_API_KEY" and os.getenv("ANTHROPIC_AUTH_TOKEN")):
        sys.exit(f"No {key} set. Copy .env.example to .env and fill it in (see README, Setup step 3).")


def complete(system: str, turns: list[dict]) -> str:
    """Return the model's text reply.

    `turns` is a list of {"role": "user" | "assistant", "content": str},
    starting and ending with a user turn.
    """
    if settings.LLM_PROVIDER == "anthropic":
        return _anthropic(system, turns)
    if settings.LLM_PROVIDER == "openai":
        return _openai(system, turns)
    sys.exit(f"LLM_PROVIDER must be 'anthropic' or 'openai', not {settings.LLM_PROVIDER!r}")


def _anthropic(system: str, turns: list[dict]) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    try:
        response = client.beta.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=16000,
            system=system,
            messages=turns,
            # Extraction is a simple task, so a moderate thinking effort is enough.
            output_config={"effort": "medium"},
            # If the model declines a request, let the API retry it on another model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        sys.exit("Anthropic rejected the API key. Check ANTHROPIC_API_KEY in .env.")
    except anthropic.NotFoundError:
        sys.exit(f"Unknown Anthropic model {settings.LLM_MODEL!r}. Check LLM_MODEL in .env.")
    except anthropic.RateLimitError:
        sys.exit("Rate limited by Anthropic. Wait a minute and run the script again.")
    except anthropic.APIStatusError as e:
        sys.exit(f"Anthropic API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Could not reach the Anthropic API. Check your internet connection.")

    if response.stop_reason == "refusal":
        raise RuntimeError("the model declined this request")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("the reply was cut off (max_tokens)")
    # The reply can also contain thinking blocks; we only want the text.
    return "".join(block.text for block in response.content if block.type == "text")


def _openai(system: str, turns: list[dict]) -> str:
    import openai

    client = openai.OpenAI()  # reads OPENAI_API_KEY
    try:
        response = client.responses.create(
            model=settings.LLM_MODEL,
            instructions=system,
            input=turns,
        )
    except openai.AuthenticationError:
        sys.exit("OpenAI rejected the API key. Check OPENAI_API_KEY in .env.")
    except openai.NotFoundError:
        sys.exit(f"Unknown OpenAI model {settings.LLM_MODEL!r}. Check LLM_MODEL in .env.")
    except openai.RateLimitError:
        sys.exit("Rate limited by OpenAI. Wait a minute and run the script again.")
    except openai.APIStatusError as e:
        sys.exit(f"OpenAI API error {e.status_code}: {e.message}")
    except openai.APIConnectionError:
        sys.exit("Could not reach the OpenAI API. Check your internet connection.")
    return response.output_text
