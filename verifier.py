import json
import time
import groq as groq_module
from groq import Groq

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are a fact-checker. Search the web for evidence about the given claim. "
    "Write your response as a JSON object in plain text (not a tool call): "
    '{"verdict": "Verified|Inaccurate|Unverified", "reason": "...", '
    '"corrected_value": "or null", "source": "url or null"}'
)

UNVERIFIED_FALLBACK = {
    "verdict": "Unverified",
    "reason": "Verification failed due to an unexpected error.",
    "corrected_value": None,
    "source": None,
}


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]).strip()
    return raw


def _extract_from_failed_generation(body: dict) -> dict | None:
    """
    When the model accidentally uses a 'json' tool call instead of plain text,
    Groq returns a 400 with the attempted generation in error.failed_generation.
    Extract the verdict from that field.
    """
    try:
        failed = body.get("error", {}).get("failed_generation", "")
        if not failed:
            return None
        parsed = json.loads(failed)
        # Shape: {"name": "json", "arguments": { verdict dict }}
        if isinstance(parsed.get("arguments"), dict):
            return parsed["arguments"]
    except Exception:
        pass
    return None


def _parse_response(message) -> dict:
    """Extract and parse the JSON verdict from a Groq chat message."""
    content = message.content

    if isinstance(content, str):
        return json.loads(_strip_fences(content))

    if isinstance(content, list):
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                return json.loads(_strip_fences(block.text))
            if isinstance(block, dict) and block.get("type") == "text":
                return json.loads(_strip_fences(block.get("text", "")))

    raise ValueError("No text block found in model response")


def verify_claim(claim: str, client: Groq) -> dict:
    """Verify a single claim via web search. Always returns a dict, never raises."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            reasoning_effort="medium",
            max_completion_tokens=8192,
            tools=[{"type": "browser_search"}],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Fact-check this claim: {claim}"},
            ],
        )
        return _parse_response(response.choices[0].message)

    except json.JSONDecodeError as e:
        return {**UNVERIFIED_FALLBACK, "reason": f"Could not parse model response as JSON: {e}"}

    except groq_module.BadRequestError as e:
        # Model tried to call a 'json' tool — extract verdict from failed_generation
        body = e.body if hasattr(e, "body") and isinstance(e.body, dict) else {}
        result = _extract_from_failed_generation(body)
        if result:
            return result
        return {**UNVERIFIED_FALLBACK, "reason": f"Bad request: {e}"}

    except Exception as e:
        err = str(e)
        if "429" in err or "rate limit" in err.lower():
            time.sleep(2)
            try:
                return verify_claim(claim, client)
            except Exception as retry_err:
                return {**UNVERIFIED_FALLBACK, "reason": f"Rate limit retry failed: {retry_err}"}
        return {**UNVERIFIED_FALLBACK, "reason": f"Verification error: {e}"}
