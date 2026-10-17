"""
Future City Fellowship AI Assistant - Phase 5K Conversation Context Backend

Goal:
- Keep Phase 2.5 Cognito/API Gateway JWT protection.
- Keep Phase 3 GPT model call.
- Keep safe, read-only GitHub repository inspection.
- Return source file paths so assistant.html can show "Sources checked".
- Optionally log usage and enforce per-user rate limits with DynamoDB.
- Improve repository source selection by following exact file mentions and referenced docs.
- Improve broad project-overview questions so source-of-truth docs are prioritized before workflow scripts.
- Add response quality guardrails so formulas/lists do not end unfinished.
- Keep scoring-method answers compact enough to finish, remove trailing fragments, and explain adjustment fields cautiously.
- Add short conversation-history context so follow-up prompts like "yeah do that" resolve correctly.
- Improve source-answer consistency so file-specific answers prioritize and cite the files they name.

Required Lambda environment variables:
- ALLOWED_ORIGIN=https://futurecityfellowship.andyyaro.com
- MAX_MESSAGE_LENGTH=2000
- GITHUB_OWNER=andyyaro
- GITHUB_REPO=Future-City-Fellowship-

Recommended Lambda environment variables:
- OPENAI_MODEL=gpt-5.4-mini
- MAX_OUTPUT_TOKENS=1200
- MAX_HISTORY_TURNS=6                              # optional; frontend also sends recent history
- GITHUB_BRANCH=main               # optional; if omitted, Lambda asks GitHub for default_branch
- MAX_REPO_FILES=6
- MAX_FILES_TO_SCAN=32
- MAX_REPO_CONTEXT_CHARS=22000
- MAX_REPO_FILE_CHARS=6500
- MAX_GITHUB_FILE_BYTES=120000
- REPO_TREE_CACHE_SECONDS=600
- USAGE_TABLE_NAME=future-city-assistant-usage   # optional; enables DynamoDB usage logging
- RATE_LIMIT_ENABLED=true                        # optional; requires USAGE_TABLE_NAME
- HOURLY_USER_LIMIT=10
- DAILY_USER_LIMIT=120
- LOG_MESSAGE_PREVIEW=false                      # optional; default avoids storing message text
- MAX_REFERENCED_FILES=4                         # optional; fetch relevant docs referenced by selected files
- ASSISTANT_SECRET_ID=future-city-assistant-secrets # optional but recommended; JSON secret containing OPENAI_API_KEY and GITHUB_TOKEN
- SECRETS_CACHE_SECONDS=300                         # optional; cache Secrets Manager values inside warm Lambda containers

Notes:
- This function uses Python standard library modules plus boto3 when DynamoDB logging or Secrets Manager is enabled.
- It is read-only. It never writes to GitHub.
- It blocks suspicious/secret file paths by name and extension.
- It reads ONLY the public paths in PUBLIC_PATH_PREFIXES / PUBLIC_EXACT_PATHS. The assistant
  has been public (no sign-in) since 2026-10-15 and the repository it reads is private, so
  this function is the boundary between the two. A blocklist was the first version of that
  boundary and it leaked: it named data/inputs/ but not the test fixtures holding copies of
  the same facility rows, and it never considered documents that name the platform's
  allowlisted accounts. A live probe on 2026-10-17 returned an allowlisted email verbatim.
  An allowlist fails closed - a new directory is unreadable until someone decides it is
  public - which is the direction a privacy boundary has to fail.
- Every fetched excerpt also has email addresses and UUIDs replaced before it reaches the
  model, so a public file that happens to quote an identifier still cannot leak it.

Source of truth: infra/assistant/lambda_function.py in the repository. Deploy steps are in
infra/assistant/README.md.
"""

import base64
import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ALLOWED_ORIGIN = "https://futurecityfellowship.andyyaro.com"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_MAX_MESSAGE_LENGTH = 2000
DEFAULT_MAX_OUTPUT_TOKENS = 1200
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
GITHUB_API_BASE = "https://api.github.com"
RAW_GITHUB_BASE = "https://raw.githubusercontent.com"

# Lambda execution environments can be reused. This small cache reduces GitHub calls.
_TREE_CACHE: Dict[str, Any] = {"expires_at": 0, "branch": None, "tree": None, "repo_meta": None}
_DDB_CLIENT = None
_SECRETS_CLIENT = None
_SECRETS_CACHE: Dict[str, Any] = {"expires_at": 0, "secret_id": None, "values": {}}

ALLOWED_EXTENSIONS = {
    ".html", ".htm", ".md", ".txt", ".csv", ".json", ".py", ".css", ".js", ".yml", ".yaml"
}

BLOCKED_PATH_PARTS = [
    ".git/", ".github/workflows/", ".venv/", "venv/", "env/", "node_modules/", "__pycache__/",
    "dist/", "build/", ".next/", ".cache/", ".terraform/", "coverage/",
    # The assistant is public (no sign-in). Facility-level raw inputs for the twelve real sites
    # stay private until the facility owners consent (repo DEC-016, human action 11), so the
    # assistant never reads them. Published, derived outputs (contract tables) stay readable.
    "data/inputs/", "data/provenance/", "site/platform/", "explorer/web/data/",
    "matlab/data/", "data/cache/",
    # Added 2026-10-17. tests/ holds fixtures that are byte-for-byte copies of the real
    # facility rows; infra/ holds the platform allowlist's deployment code; docs/operations/
    # and docs/human-actions/ are the program's working notes (decisions, ledgers, contact
    # maps), not visitor material.
    "tests/", "infra/", "docs/operations/", "docs/human-actions/", "presentation/", "excel/",
    ".github/",
]

#: The ONLY paths the public assistant may read. Checked after BLOCKED_PATH_PARTS, so a
#: blocked sub-directory of an allowed prefix (matlab/data/, explorer/web/data/) stays blocked.
#: Lower-case, repository-relative.
PUBLIC_PATH_PREFIXES = (
    "docs/", "src/", "site/www/", "reports/", "dashboard/", "matlab/", "explorer/",
    "data/contract/", "data/anchors/", "data/synthetic/", "data/schema/", "data/intake/",
    "data/observed/", "scripts/build_", "scripts/check_",
)

#: Individual public files outside those prefixes. An exact entry is still subject to the
#: name and extension rules, but it is allowed even where a blocked directory contains it -
#: the reproduction guide is visitor material that happens to live under docs/operations/.
PUBLIC_EXACT_PATHS = {
    "readme.md", "changelog.md", "contributing.md", "third_party_licences.md",
    "data/readme.md", "docs/operations/reproduction-guide.md", "scripts/intake_review.py",
    "scripts/readme.md",
}

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

BLOCKED_NAME_PATTERNS = [
    ".env", "secret", "secrets", "credential", "credentials", "token", "apikey", "api_key",
    "private", "id_rsa", ".pem", ".key", ".p12", ".pfx", "aws_access_key", "aws_secret",
]

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from", "how",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "our", "the", "this", "to", "what", "when",
    "where", "which", "who", "why", "with", "about", "tell", "show", "explain", "project", "assistant",
    "future", "city", "fellowship", "gmu", "model", "more", "info", "information", "overview", "summary"
}

PROJECT_BASE_CONTEXT = """The website is the Future City GMU / Future City Fellowship project.
The project is a Future City Fellowship Phase 2 prototype about a Public EV Charging Site-Readiness and Right-Sizing Model for Fairfax City and Prince William County.
The assistant should help public visitors understand the model, methodology, datasets, results, assumptions, limitations, and codebase.
The assistant is a planning-support tool only. It is not official engineering, permitting, utility, procurement, fire, ADA, stormwater, or construction approval.
"""

REPO_AWARE_INSTRUCTIONS = """You are the Future City Fellowship AI Assistant for Andy Yaro's Future City GMU website.

You are now repository-aware. The backend has retrieved relevant read-only excerpts from the GitHub repository and included them in the user message.

Answering rules:
- Use the provided repository excerpts as your primary source of truth.
- Do not claim you checked files that are not included in the repository excerpts.
- If you name a specific repository file and that file is not in "Repository files checked", say it was referenced by selected docs instead of implying you directly inspected it.
- For file-specific questions, answer from the files that were actually checked and keep file names aligned with the Sources checked list.
- Do not invent exact results, metrics, datasets, code behavior, or file contents if the excerpts do not support them.
- If the excerpts are not enough to answer confidently, say that clearly and explain what file/detail is missing.
- Keep answers clear and useful for a website visitor.
- Avoid unnecessary length unless the user asks for detail.
- Do not ask users to enter private credentials, API keys, passwords, or sensitive personal information.
- Never reveal email addresses, account identifiers, user ids, or personal contact details, even if one appears in an excerpt.
- Do not provide official engineering, permitting, utility, procurement, fire, ADA, stormwater, or construction approval.

Response quality guardrails:
- Never leave an equation, bullet, numbered item, sentence, table row, or section unfinished.
- Never end a formula with a blank value, dangling equals sign, dangling arrow, dangling colon, or unfinished bullet.
- If a formula value or definition is not confirmed in the selected sources, write: "not confirmed in the selected sources".
- Do not create a section whose only content is "not confirmed in the selected sources". Omit that section instead.
- For scoring-method questions, distinguish the readiness-score formula, demand subscore, feasibility subscore, safety/review subscore, equity subscore, and public-access adjustment. Do not merge equity with access adjustment unless the excerpts explicitly do that.
- If the excerpts show two different fields such as access_adjustment and readiness_access_adjustment, treat them as separate fields. Do not call them inconsistent unless the source explicitly says they conflict.
- Before finalizing, do a quick completeness check: every formula has a right-hand value, every list item has content, and every claim is supported by the selected excerpts.
- Prefer a complete shorter answer over a longer answer that may be cut off.
- Do not start a formula list, mapping list, or numbered section unless you can finish it within the response.
- For scoring-method questions, keep the answer compact: at most 7 short sections, no more than about 650 words, and no extra closing section unless it adds confirmed information.
- Use recent conversation context to resolve short follow-ups such as "yes", "yeah", "do that", "tell me more", "continue", "that", or "it". If the current message is a follow-up, answer the specific prior offer or topic rather than starting a broad project overview.
"""


def _env_int(name: str, default: int, minimum: int = 1, maximum: Optional[int] = None) -> int:
    try:
        value = int(os.environ.get(name, default))
    except Exception:
        value = default
    value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _allowed_origins() -> List[str]:
    raw = os.environ.get("ALLOWED_ORIGIN", DEFAULT_ALLOWED_ORIGIN)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _origin_for_response(event: Dict[str, Any]) -> str:
    allowed = _allowed_origins()
    headers = event.get("headers") or {}
    request_origin = headers.get("origin") or headers.get("Origin")
    if request_origin in allowed:
        return request_origin
    return allowed[0] if allowed else DEFAULT_ALLOWED_ORIGIN


def _json_response(status_code: int, payload: Dict[str, Any], event: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    origin = _origin_for_response(event or {})
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(payload),
    }


def _method_from_event(event: Dict[str, Any]) -> str:
    return (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "POST"
    ).upper()


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    if isinstance(raw_body, dict):
        return raw_body
    return json.loads(raw_body)


def _sanitize_history(raw_history: Any) -> List[Dict[str, str]]:
    """Keep only a small, safe text history window from the browser.

    This is not long-term memory. It only helps resolve immediate follow-ups like
    "yeah do that" by giving the model the last few user/assistant turns.
    """
    if not isinstance(raw_history, list):
        return []

    max_turns = _env_int("MAX_HISTORY_TURNS", 6, 0, 10)
    max_chars_per_turn = _env_int("MAX_HISTORY_CHARS_PER_TURN", 800, 120, 1600)
    cleaned: List[Dict[str, str]] = []

    for item in raw_history[-max_turns:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        content = re.sub(r"\s+", " ", content)[:max_chars_per_turn]
        cleaned.append({"role": role, "content": content})

    return cleaned


def _is_short_followup(message: str) -> bool:
    q = re.sub(r"[^a-z0-9\s]", " ", (message or "").lower())
    q = re.sub(r"\s+", " ", q).strip()
    if not q:
        return False
    direct = {
        "yes", "yeah", "yep", "sure", "ok", "okay", "do it", "do that", "yeah do that",
        "yes do that", "please do", "continue", "go on", "tell me more", "explain that",
        "what about that", "that", "it", "next", "go deeper", "break it down"
    }
    if q in direct:
        return True
    return len(q.split()) <= 5 and any(term in q for term in ["that", "it", "continue", "more", "next", "deeper"])


def _history_text_for_prompt(history: List[Dict[str, str]]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history[-6:]:
        label = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{label}: {turn['content']}")
    return "\n".join(lines)


def _contextual_selection_query(message: str, history: List[Dict[str, str]]) -> str:
    """Build a richer repo-search query when the user sends a vague follow-up."""
    message = (message or "").strip()
    if not history:
        return message

    # Always add a little prior context, but make short follow-ups rely more heavily
    # on the prior assistant offer/topic so the source selector fetches the right docs.
    recent_parts = []
    for turn in history[-4:]:
        recent_parts.append(f"{turn['role']}: {turn['content']}")

    recent = "\n".join(recent_parts)
    if _is_short_followup(message):
        return f"Follow-up user question: {message}\nRecent conversation context:\n{recent}"

    return f"Current user question: {message}\nRecent context:\n{recent[-1800:]}"


def _auth_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
        or {}
    )


def _user_from_claims(claims: Dict[str, Any]) -> Dict[str, str]:
    return {
        "sub": str(claims.get("sub", "unknown-user")),
        "email": str(claims.get("email", "unknown-email")),
        "username": str(claims.get("cognito:username") or claims.get("username") or claims.get("email") or "unknown-user"),
    }


def _anonymous_user(event: Dict[str, Any]) -> Dict[str, str]:
    ip = str(((event.get("requestContext") or {}).get("http") or {}).get("sourceIp") or "unknown-ip")
    salt = os.environ.get("ANON_ID_SALT", "future-city-assistant")
    digest = hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()[:16]
    return {"sub": f"anon-{digest}", "email": "anonymous", "username": "anonymous"}


def _truthy_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _dynamodb_client():
    global _DDB_CLIENT
    if _DDB_CLIENT is None:
        import boto3  # Included in AWS Lambda Python runtimes; imported lazily so the assistant still runs if logging is disabled.
        _DDB_CLIENT = boto3.client("dynamodb")
    return _DDB_CLIENT


def _usage_table_name() -> str:
    return os.environ.get("USAGE_TABLE_NAME", "").strip()

def _secrets_manager_client():
    global _SECRETS_CLIENT
    if _SECRETS_CLIENT is None:
        import boto3  # Included in AWS Lambda Python runtimes; imported lazily so secrets remain optional.
        _SECRETS_CLIENT = boto3.client("secretsmanager")
    return _SECRETS_CLIENT


def _assistant_secret_id() -> str:
    """Optional Secrets Manager secret name/ARN for sensitive values.

    Expected JSON SecretString example:
    {
      "OPENAI_API_KEY": "sk-...",
      "GITHUB_TOKEN": "github_pat_..."
    }
    """
    return (
        os.environ.get("ASSISTANT_SECRET_ID")
        or os.environ.get("SECRETS_MANAGER_SECRET_ID")
        or os.environ.get("ASSISTANT_SECRETS_ARN")
        or ""
    ).strip()


def _assistant_secrets() -> Dict[str, str]:
    secret_id = _assistant_secret_id()
    if not secret_id:
        return {}

    now = time.time()
    cache_seconds = _env_int("SECRETS_CACHE_SECONDS", 300, 0, 3600)
    cached_values = _SECRETS_CACHE.get("values") or {}
    if (
        _SECRETS_CACHE.get("secret_id") == secret_id
        and cached_values
        and _SECRETS_CACHE.get("expires_at", 0) > now
    ):
        return dict(cached_values)

    response = _secrets_manager_client().get_secret_value(SecretId=secret_id)
    raw = response.get("SecretString") or "{}"
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    values = {str(k): str(v) for k, v in parsed.items() if v is not None}
    _SECRETS_CACHE["secret_id"] = secret_id
    _SECRETS_CACHE["values"] = values
    _SECRETS_CACHE["expires_at"] = now + cache_seconds
    return dict(values)


def _secret_or_env(name: str, default: str = "") -> str:
    """Read non-sensitive env vars normally, but allow sensitive vars to live in Secrets Manager.

    For a smooth rollout, direct Lambda environment variables still work as a fallback/override.
    After Secrets Manager is verified, remove OPENAI_API_KEY and GITHUB_TOKEN from Lambda env vars.
    """
    value = os.environ.get(name)
    if value:
        return value.strip()

    secrets = _assistant_secrets()
    value = secrets.get(name)
    if value:
        return value.strip()

    return default



def _now_parts() -> Dict[str, Any]:
    now = time.time()
    gmt = time.gmtime(now)
    return {
        "epoch": now,
        "epochMs": int(now * 1000),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", gmt),
        "date": time.strftime("%Y-%m-%d", gmt),
        "hour": time.strftime("%Y-%m-%dT%H", gmt),
    }


def _message_hash(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8", errors="ignore")).hexdigest()


def _json_attr(value: Any, max_chars: int = 4000) -> Dict[str, str]:
    text = json.dumps(value, ensure_ascii=False, default=str)
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    return {"S": text}


def _increment_usage_counter(table_name: str, pk: str, sk: str, user: Dict[str, str], ttl_epoch: int) -> int:
    now = _now_parts()["iso"]
    response = _dynamodb_client().update_item(
        TableName=table_name,
        Key={"pk": {"S": pk}, "sk": {"S": sk}},
        UpdateExpression=(
            "SET firstSeenAt = if_not_exists(firstSeenAt, :now), "
            "updatedAt = :now, expiresAt = :ttl, userEmail = :email, userSub = :sub "
            "ADD usageCount :one"
        ),
        ExpressionAttributeValues={
            ":one": {"N": "1"},
            ":now": {"S": now},
            ":ttl": {"N": str(ttl_epoch)},
            ":email": {"S": user.get("email", "unknown-email")},
            ":sub": {"S": user.get("sub", "unknown-user")},
        },
        ReturnValues="UPDATED_NEW",
    )
    attrs = response.get("Attributes", {})
    return int(attrs.get("usageCount", {}).get("N", "0"))


def _check_rate_limits(user: Dict[str, str]) -> Dict[str, Any]:
    """Optional DynamoDB-backed per-user hourly/daily rate limits.

    If RATE_LIMIT_ENABLED is false or USAGE_TABLE_NAME is empty, this is a no-op.
    """
    table_name = _usage_table_name()
    if not table_name or not _truthy_env("RATE_LIMIT_ENABLED", False):
        return {"allowed": True, "rateLimitEnabled": False}

    hourly_limit = _env_int("HOURLY_USER_LIMIT", 30, 1, 10000)
    daily_limit = _env_int("DAILY_USER_LIMIT", 120, 1, 100000)
    parts = _now_parts()
    sub = user.get("sub", "unknown-user")
    # Keep counter rows briefly beyond the window for audit/debug.
    ttl_epoch = int(parts["epoch"] + 60 * 60 * 24 * 8)

    try:
        hourly_pk = f"USER#{sub}#HOUR#{parts['hour']}"
        hourly_count = _increment_usage_counter(table_name, hourly_pk, "COUNT#HOUR", user, ttl_epoch)
        if hourly_count > hourly_limit:
            return {
                "allowed": False,
                "rateLimitEnabled": True,
                "window": "hour",
                "count": hourly_count,
                "limit": hourly_limit,
                "answer": f"You have reached the assistant limit of {hourly_limit} messages per hour. Please try again later.",
            }

        global_limit = _env_int("GLOBAL_DAILY_LIMIT", 1500, 1, 1000000)
        global_count = _increment_usage_counter(table_name, f"GLOBAL#DATE#{parts['date']}", "COUNT#DAY", user, ttl_epoch)
        if global_count > global_limit:
            return {
                "allowed": False,
                "rateLimitEnabled": True,
                "window": "global-day",
                "count": global_count,
                "limit": global_limit,
                "answer": "The assistant has reached its daily limit for all visitors. Please try again tomorrow.",
            }

        daily_pk = f"USER#{sub}#DATE#{parts['date']}"
        daily_count = _increment_usage_counter(table_name, daily_pk, "COUNT#DAY", user, ttl_epoch)
        if daily_count > daily_limit:
            return {
                "allowed": False,
                "rateLimitEnabled": True,
                "window": "day",
                "count": daily_count,
                "limit": daily_limit,
                "answer": f"You have reached the assistant limit of {daily_limit} messages today. Please try again later.",
            }

        return {
            "allowed": True,
            "rateLimitEnabled": True,
            "hourlyCount": hourly_count,
            "hourlyLimit": hourly_limit,
            "dailyCount": daily_count,
            "dailyLimit": daily_limit,
        }
    except Exception as exc:
        print(json.dumps({
            "event": "rate_limit_check_error",
            "error": str(exc),
            "userSub": user.get("sub"),
            "userEmail": user.get("email"),
        }))
        if _truthy_env("RATE_LIMIT_FAIL_CLOSED", False):
            return {
                "allowed": False,
                "rateLimitEnabled": True,
                "window": "unknown",
                "count": 0,
                "limit": 0,
                "answer": "The assistant usage guard is temporarily unavailable. Please try again later.",
            }
        return {"allowed": True, "rateLimitEnabled": True, "rateLimitWarning": "rate_limit_check_failed_open"}


def _log_usage_event(
    *,
    status: str,
    user: Dict[str, str],
    session_id: str,
    message: str,
    model: str,
    sources: List[str],
    latency_ms: int = 0,
    repo_debug: Optional[Dict[str, Any]] = None,
    usage: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Optional DynamoDB usage logging. Does not block the user response."""
    table_name = _usage_table_name()
    if not table_name:
        return

    try:
        parts = _now_parts()
        sub = user.get("sub", "unknown-user")
        request_id = hashlib.sha1(f"{session_id}:{parts['epochMs']}:{message[:64]}".encode("utf-8", errors="ignore")).hexdigest()[:16]
        item = {
            "pk": {"S": f"USER#{sub}#DATE#{parts['date']}"},
            "sk": {"S": f"MSG#{parts['epochMs']}#{request_id}"},
            "createdAt": {"S": parts["iso"]},
            "expiresAt": {"N": str(int(parts["epoch"] + 60 * 60 * 24 * _env_int("USAGE_LOG_TTL_DAYS", 90, 1, 3650)))},
            "status": {"S": status},
            "phase": {"S": "phase_5m_direct_file_source_alignment"},
            "userSub": {"S": sub},
            "userEmail": {"S": user.get("email", "unknown-email")},
            "username": {"S": user.get("username", "unknown-user")},
            "sessionId": {"S": session_id[:128]},
            "model": {"S": model or "unknown-model"},
            "messageLength": {"N": str(len(message))},
            "messageHash": {"S": _message_hash(message)},
            "sourceCount": {"N": str(len(sources or []))},
            "sourcesJson": _json_attr(sources or [], 2000),
            "latencyMs": {"N": str(max(0, int(latency_ms)))},
        }

        if usage:
            item["openaiUsageJson"] = _json_attr(usage, 2000)
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                if isinstance(usage.get(key), int):
                    item[key] = {"N": str(usage[key])}

        if repo_debug:
            item["repoBranch"] = {"S": str(repo_debug.get("branch") or "")[:128]}
            item["repoDebugJson"] = _json_attr(repo_debug, 3500)

        if error:
            item["error"] = {"S": str(error)[:800]}

        if _truthy_env("LOG_MESSAGE_PREVIEW", False):
            item["messagePreview"] = {"S": message[:500]}

        _dynamodb_client().put_item(TableName=table_name, Item=item)
    except Exception as exc:
        print(json.dumps({
            "event": "usage_log_error",
            "error": str(exc),
            "userSub": user.get("sub"),
            "userEmail": user.get("email"),
        }))


def _github_headers(raw: bool = False) -> Dict[str, str]:
    headers = {
        "User-Agent": "future-city-fellowship-assistant",
        "Accept": "application/vnd.github+json" if not raw else "application/vnd.github.raw",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _secret_or_env("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict[str, Any]:
    request = urllib.request.Request(url, method="GET", headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_get_text(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> str:
    request = urllib.request.Request(url, method="GET", headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
        return data.decode("utf-8", errors="replace")


def _repo_owner_repo() -> Tuple[str, str]:
    owner = os.environ.get("GITHUB_OWNER", "andyyaro").strip()
    repo = os.environ.get("GITHUB_REPO", "Future-City-Fellowship-").strip()
    if not owner or not repo:
        raise RuntimeError("GITHUB_OWNER and GITHUB_REPO must be configured.")
    return owner, repo


def _repo_default_branch(owner: str, repo: str) -> str:
    now = time.time()
    cached = _TREE_CACHE.get("repo_meta")
    if cached and _TREE_CACHE.get("repo_meta_expires_at", 0) > now:
        return str(cached.get("default_branch") or "main")

    url = f"{GITHUB_API_BASE}/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
    payload = _http_get_json(url, headers=_github_headers(), timeout=10)
    _TREE_CACHE["repo_meta"] = payload
    _TREE_CACHE["repo_meta_expires_at"] = now + _env_int("REPO_TREE_CACHE_SECONDS", 600, 60, 3600)
    return str(payload.get("default_branch") or "main")


def _repo_branch(owner: str, repo: str) -> str:
    branch = os.environ.get("GITHUB_BRANCH", "").strip()
    if branch:
        return branch
    return _repo_default_branch(owner, repo)


def _fetch_repo_tree(owner: str, repo: str, branch: str) -> List[Dict[str, Any]]:
    now = time.time()
    cache_seconds = _env_int("REPO_TREE_CACHE_SECONDS", 600, 60, 3600)
    if _TREE_CACHE.get("tree") is not None and _TREE_CACHE.get("branch") == branch and _TREE_CACHE.get("expires_at", 0) > now:
        return _TREE_CACHE["tree"]

    quoted_owner = urllib.parse.quote(owner)
    quoted_repo = urllib.parse.quote(repo)
    quoted_branch = urllib.parse.quote(branch, safe="")
    url = f"{GITHUB_API_BASE}/repos/{quoted_owner}/{quoted_repo}/git/trees/{quoted_branch}?recursive=1"

    try:
        payload = _http_get_json(url, headers=_github_headers(), timeout=12)
    except urllib.error.HTTPError as exc:
        # If an explicitly configured branch fails, try repository default branch once.
        if exc.code == 404 and os.environ.get("GITHUB_BRANCH", "").strip():
            fallback_branch = _repo_default_branch(owner, repo)
            url = f"{GITHUB_API_BASE}/repos/{quoted_owner}/{quoted_repo}/git/trees/{urllib.parse.quote(fallback_branch, safe='')}?recursive=1"
            payload = _http_get_json(url, headers=_github_headers(), timeout=12)
            branch = fallback_branch
        else:
            raise

    if payload.get("truncated"):
        print(json.dumps({"event": "github_tree_truncated", "owner": owner, "repo": repo, "branch": branch}))

    tree = payload.get("tree", []) or []
    _TREE_CACHE["tree"] = tree
    _TREE_CACHE["branch"] = branch
    _TREE_CACHE["expires_at"] = now + cache_seconds
    return tree


def _path_ext(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    if "." not in base:
        return ""
    return "." + base.rsplit(".", 1)[-1].lower()


def _is_public_path(lower: str) -> bool:
    """Whether a lower-case repository path is one the public assistant may read at all."""
    if lower in PUBLIC_EXACT_PATHS:
        return True
    if any(part in lower for part in BLOCKED_PATH_PARTS):
        return False
    return lower.startswith(PUBLIC_PATH_PREFIXES)


def _redact_identifiers(text: str) -> str:
    """Remove email addresses and UUIDs from an excerpt before it reaches the model."""
    text = EMAIL_PATTERN.sub("[email removed]", text)
    return UUID_PATTERN.sub("[id removed]", text)


def _is_allowed_repo_path(path: str, item: Optional[Dict[str, Any]] = None) -> bool:
    normalized = path.replace("\\", "/")
    lower = normalized.lower().strip("/")

    if item and item.get("type") != "blob":
        return False

    if not _is_public_path(lower):
        return False

    for pattern in BLOCKED_NAME_PATTERNS:
        if pattern in lower:
            return False

    ext = _path_ext(lower)
    if ext not in ALLOWED_EXTENSIONS:
        return False

    size_limit = _env_int("MAX_GITHUB_FILE_BYTES", 120000, 10000, 500000)

    # Important source-of-truth files should remain eligible even if they are
    # slightly larger than the normal scan limit. They are still excerpted later,
    # so allowing them here does not mean the full file is sent to the model.
    important_paths = set()
    for global_name in [
        "SOURCE_OF_TRUTH_FILES",
        "BROAD_OVERVIEW_FILES",
        "TABLEAU_EXPORT_FILES",
        "SCORING_METHOD_FILES",
    ]:
        for candidate in globals().get(global_name, []) or []:
            important_paths.add(str(candidate).replace("\\", "/").strip("/").lower())

    if item and isinstance(item.get("size"), int) and item["size"] > size_limit:
        important_size_limit = _env_int("MAX_GITHUB_IMPORTANT_FILE_BYTES", 500000, 10000, 1000000)
        if lower not in important_paths or item["size"] > important_size_limit:
            return False

    return True


def _keywords(question: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9_\-]{3,}", question.lower())
    cleaned: List[str] = []
    for word in words:
        word = word.strip("-_")
        if not word or word in STOPWORDS:
            continue
        if word not in cleaned:
            cleaned.append(word)
    return cleaned[:18]


def _is_general_project_question(question: str) -> bool:
    """Detect broad website-visitor questions that need source-of-truth docs first.

    These questions should not be answered mainly from runner/check scripts.
    They should prioritize README and docs files that explain the project,
    methodology, data, limitations, and outputs in visitor-friendly terms.
    """
    q = " ".join(question.lower().split())
    triggers = [
        "tell me more about this project",
        "tell me about this project",
        "tell me more",
        "what does this project",
        "what is this project",
        "what is the project",
        "what is this about",
        "what is it about",
        "describe this project",
        "explain this project",
        "explain the project",
        "project overview",
        "overview of the project",
        "summarize the project",
        "summary of the project",
        "what does the model",
        "how does the model",
        "how does this work",
        "what is future city",
        "what is the assistant",
    ]
    if any(t in q for t in triggers):
        return True

    # Extra broad-pattern catch: a very short question mentioning the project/model
    # with no specific technical topic is probably an overview request.
    words = re.findall(r"[a-zA-Z0-9_\-]{3,}", q)
    if len(words) <= 8 and any(w in q for w in ["project", "model", "prototype", "assistant"]):
        broad_words = {"tell", "more", "about", "what", "this", "project", "model", "prototype", "assistant", "explain", "describe", "overview", "summary"}
        if all((w in broad_words) for w in words):
            return True
    return False


def _is_scoring_question(question: str) -> bool:
    q = " ".join(question.lower().split())
    triggers = [
        "score", "scoring", "scoring method", "formula", "readiness score",
        "demand subscore", "feasibility subscore", "safety subscore",
        "equity subscore", "ranking", "rank", "tier", "recommendation tier"
    ]
    return any(trigger in q for trigger in triggers)


def _is_tableau_export_question(question: str) -> bool:
    q = " ".join(question.lower().split())
    tableau_terms = ["tableau", "workbook", "dashboard", "visual", "visualization", "chart", "export", "exports", "csv", "csvs"]
    file_terms = ["file", "files", "support", "supports", "source", "sources", "script", "scripts", "generate", "generated", "check", "validate"]
    return any(term in q for term in tableau_terms) and any(term in q for term in file_terms)


def _score_path(path: str, keywords: List[str], general: bool) -> int:
    lower = path.lower()
    score = 0

    for kw in keywords:
        if kw in lower:
            score += 8

    basename = lower.rsplit("/", 1)[-1]
    if basename == "readme.md":
        score += 10
    if basename in {"index.html", "dashboard.html", "results.html", "methodology.html", "assistant.html"}:
        score += 8
    if "report" in lower or "reports/" in lower:
        score += 5
    if "data" in lower or lower.endswith(".csv"):
        score += 3
    if "src" in lower or lower.endswith(".py"):
        score += 3

    if general:
        overview_rank = {p.lower(): i for i, p in enumerate(BROAD_OVERVIEW_FILES)}
        if lower in overview_rank:
            # Strong boost for explanatory docs on broad overview questions.
            score += 320 - min(overview_rank[lower] * 10, 90)
        if basename in {"readme.md", "index.html", "methodology.html", "dashboard.html", "results.html"}:
            score += 24
        if "methodology" in lower or "results" in lower or "dashboard" in lower:
            score += 12
        if lower.startswith("docs/") and lower.endswith(".md"):
            score += 35
        if lower.startswith("src/") and lower.endswith(".py"):
            # Runner/check scripts are useful follow-up sources, but for broad
            # visitor overviews they should not crowd out methodology/docs.
            score -= 35


    # Scoring/ranking questions should pull actual scoring docs/code before generic README files.
    scoring_terms = {"score", "scoring", "readiness", "formula", "rank", "ranking", "tier", "recommendation"}
    if any((kw in scoring_terms or "score" in kw or "readiness" in kw) for kw in keywords):
        scoring_rank = {p.lower(): i for i, p in enumerate(SCORING_METHOD_FILES)} if "SCORING_METHOD_FILES" in globals() else {}
        if lower in scoring_rank:
            score += 420 - min(scoring_rank[lower] * 20, 140)
        if lower.startswith("docs/") and any(term in lower for term in ["methodology", "data_dictionary", "workflow", "scenario", "right_sizing", "electrical"]):
            score += 85
        if lower.startswith("src/") and lower.endswith(".py") and any(term in lower for term in ["model", "score", "scoring", "run_v2", "sensitivity", "profile"]):
            score += 90
        if basename == "readme.md" and not lower in scoring_rank:
            score -= 10

    tableau_terms = {"tableau", "workbook", "dashboard", "visual", "visualization", "chart", "export", "exports", "csv", "csvs"}
    if any((kw in tableau_terms or "tableau" in kw or "export" in kw) for kw in keywords):
        tableau_rank = {p.lower(): i for i, p in enumerate(TABLEAU_EXPORT_FILES)} if "TABLEAU_EXPORT_FILES" in globals() else {}
        if lower in tableau_rank:
            score += 430 - min(tableau_rank[lower] * 25, 150)
        if lower.startswith("src/") and lower.endswith(".py") and any(term in lower for term in ["tableau", "export", "check"]):
            score += 115
        if lower.startswith("docs/") and any(term in lower for term in ["workflow", "data_dictionary", "methodology"]):
            score += 60

    return score


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_text_for_context(path: str, text: str) -> str:
    ext = _path_ext(path)
    if ext in {".html", ".htm"}:
        return _redact_identifiers(_strip_html(text))
    if ext in {".json", ".yml", ".yaml"}:
        # Keep structure but trim whitespace noise.
        return _redact_identifiers(re.sub(r"\n{3,}", "\n\n", text).strip())
    return _redact_identifiers(text.strip())


def _fetch_file_text(owner: str, repo: str, branch: str, path: str) -> str:
    quoted_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    token = _secret_or_env("GITHUB_TOKEN", "").strip()

    if token:
        # This supports both public and private repos when token has read access.
        url = f"{GITHUB_API_BASE}/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/contents/{quoted_path}?ref={urllib.parse.quote(branch, safe='')}"
        return _http_get_text(url, headers=_github_headers(raw=True), timeout=12)

    # Public-repo path. This avoids extra contents-API calls for every file.
    raw_url = f"{RAW_GITHUB_BASE}/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/{urllib.parse.quote(branch, safe='')}/{quoted_path}"
    return _http_get_text(raw_url, headers={"User-Agent": "future-city-fellowship-assistant"}, timeout=12)


def _content_score(path: str, text: str, keywords: List[str], general: bool, path_score: int) -> int:
    lower = text.lower()
    score = path_score
    for kw in keywords:
        count = lower.count(kw)
        if count:
            score += min(count, 12) * 3
    if general:
        for term in ["ev charging", "site", "readiness", "right-sizing", "methodology", "dashboard", "results", "planning"]:
            if term in lower:
                score += 4
    return score


def _excerpt_text(text: str, keywords: List[str], max_chars: int) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= max_chars:
        return text

    lower = text.lower()
    positions = [lower.find(kw) for kw in keywords if kw and lower.find(kw) >= 0]
    if positions:
        first = min(positions)
        start = max(0, first - max_chars // 4)
    else:
        start = 0
    excerpt = text[start:start + max_chars]
    if start > 0:
        excerpt = "..." + excerpt
    if start + max_chars < len(text):
        excerpt = excerpt + "..."
    return excerpt.strip()


SOURCE_OF_TRUTH_FILES = [
    "README.md",
    "docs/START_HERE.md",
    "docs/WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md",
    "docs/GLOSSARY.md",
    "reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md",
    "data/contract/v1/README.md",
    "docs/README.md",
]

# For broad visitor questions like "tell me more about this project", prefer
# these explanatory files before operational scripts such as run/check/export code.
BROAD_OVERVIEW_FILES = [
    "README.md",
    "docs/START_HERE.md",
    "docs/WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md",
    "docs/GLOSSARY.md",
    "docs/README.md",
    "src/README.md",
    "data/README.md",
]

# For Tableau/export/file-support questions, force the selector to include
# the actual export builder/checker files alongside explanatory docs.
TABLEAU_EXPORT_FILES = [
    "dashboard/README.md",
    "dashboard/tableau/CAPABILITY_GAP.md",
    "dashboard/tableau/EMBED.md",
    "scripts/build_tableau_workbook.py",
    "data/contract/v1/README.md",
]

# For questions like "walk me through the scoring method", force the
# selector to include both explanatory docs and likely implementation files.
SCORING_METHOD_FILES = [
    "README.md",                      # carries the canonical ranking (FFX004 53.4) and its caveats
    "src/fcf_m2/scoring.py",
    "src/fcf_m2/confidence.py",
    "src/fcf_m2/right_sizing.py",
    "data/anchors/anchor_set_v1.json",
    "docs/GLOSSARY.md",
    "docs/migration-from-v2.md",
    "src/README.md",
]

TOPIC_FILE_HINTS = [
    (["methodology", "method", "methods", "how it works"], ["reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md", "docs/START_HERE.md", "docs/GLOSSARY.md"]),
    (["data source", "sources", "dataset", "datasets", "where does the data", "data came"], ["data/README.md", "docs/methodology/current-facts-source-register.md", "data/contract/v1/README.md"]),
    (["data dictionary", "field", "fields", "columns", "schema"], ["docs/GLOSSARY.md", "data/contract/v1/README.md", "matlab/DATA_DICTIONARY.md"]),
    (["workflow", "current workflow", "pipeline", "run", "generate"], ["docs/WORKFLOW_STEPS.md", "docs/operations/reproduction-guide.md", "docs/README.md"]),
    (["electrical", "transformer", "service", "load", "capacity", "risk"], ["docs/WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md", "reports/milestone-2/RISK_REGISTER.md", "matlab/README.md"]),
    (["right-sizing", "right sizing", "ports", "port sizing", "how many chargers", "2036", "2046", "2056", "horizon"], ["src/fcf_m2/right_sizing.py", "README.md", "docs/GLOSSARY.md"]),
    (["cost", "costs", "economics", "npv", "lifecycle", "budget"], ["src/fcf_m2/economics.py", "reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md"]),
    (["emissions", "co2", "co2e", "carbon", "egrid", "environment"], ["src/fcf_m2/emissions.py", "reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md"]),
    (["standard", "standards", "ul 2594", "ul 3600", "nec", "code", "ahj", "fire"], ["docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md", "docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md"]),
    (["nfc", "tag", "tags", "field form", "capture"], ["docs/nfc/README.md", "docs/nfc/PILOT_PLAN.md"]),
    (["tableau", "workbook", "dashboard", "visual", "visualization", "chart", "export", "exports", "csv", "csvs"], TABLEAU_EXPORT_FILES),
    (["score", "scoring", "scoring method", "formula", "readiness score", "rank", "ranking", "readiness", "tier", "recommendation"], SCORING_METHOD_FILES),
]

FILE_REF_PATTERN = re.compile(
    r"(?i)(?:`([^`]{1,180})`|\[?((?:(?:[A-Za-z0-9_.-]+/)+)?[A-Za-z0-9_.-]+\.(?:md|py|csv|json|html|htm|txt|yml|yaml|js|css))\]?)"
)


def _allowed_path_indexes(allowed_items: List[Dict[str, Any]]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    full: Dict[str, str] = {}
    by_base: Dict[str, List[str]] = {}
    for item in allowed_items:
        path = str(item.get("path", ""))
        if not path:
            continue
        norm = path.replace("\\", "/").strip("/")
        lower = norm.lower()
        full[lower] = norm
        base = lower.rsplit("/", 1)[-1]
        by_base.setdefault(base, []).append(norm)
    return full, by_base


def _dedupe_paths(paths: List[str]) -> List[str]:
    seen = set()
    result = []
    for path in paths:
        norm = path.replace("\\", "/").strip("/")
        key = norm.lower()
        if norm and key not in seen:
            seen.add(key)
            result.append(norm)
    return result


def _clean_file_reference(ref: str) -> str:
    ref = (ref or "").strip().strip("'\"“”‘’.,;:()[]{}<>")
    ref = ref.split("#", 1)[0].split("?", 1)[0]
    ref = ref.replace("\\", "/")
    while ref.startswith("./"):
        ref = ref[2:]
    return ref.strip("/")


def _resolve_repo_file_reference(
    ref: str,
    source_path: Optional[str],
    full_index: Dict[str, str],
    basename_index: Dict[str, List[str]],
) -> List[str]:
    """Resolve a user/repo file reference to actual allowed repo paths.

    Handles exact paths like docs/METHODOLOGY.md and relative references like
    METHODOLOGY.md from docs/README.md -> docs/METHODOLOGY.md.
    """
    ref = _clean_file_reference(ref)
    if not ref:
        return []

    candidates: List[str] = []
    lower = ref.lower()

    if lower in full_index:
        candidates.append(full_index[lower])

    if source_path and "/" not in ref:
        source_dir = source_path.replace("\\", "/").rsplit("/", 1)[0] if "/" in source_path else ""
        if source_dir:
            relative = f"{source_dir}/{ref}".lower()
            if relative in full_index:
                candidates.append(full_index[relative])

    # Also match by basename. This is what lets a question like
    # "What does METHODOLOGY.md say?" find docs/METHODOLOGY.md.
    base = lower.rsplit("/", 1)[-1]
    for path in basename_index.get(base, []):
        candidates.append(path)

    # If the user omitted a directory but the ending path is unique enough, match suffix.
    if "/" in lower:
        for key, path in full_index.items():
            if key.endswith("/" + lower):
                candidates.append(path)

    return _dedupe_paths(candidates)


def _extract_file_mentions(text: str) -> List[str]:
    mentions: List[str] = []
    for match in FILE_REF_PATTERN.finditer(text or ""):
        ref = match.group(1) or match.group(2) or ""
        cleaned = _clean_file_reference(ref)
        if cleaned and _path_ext(cleaned.lower()) in ALLOWED_EXTENSIONS:
            mentions.append(cleaned)
    return _dedupe_paths(mentions)


def _topic_hint_paths(question: str, full_index: Dict[str, str], basename_index: Dict[str, List[str]]) -> List[str]:
    q = question.lower()
    hinted: List[str] = []

    for triggers, paths in TOPIC_FILE_HINTS:
        if any(trigger in q for trigger in triggers):
            for path in paths:
                hinted.extend(_resolve_repo_file_reference(path, None, full_index, basename_index))

    if _is_general_project_question(question):
        for path in BROAD_OVERVIEW_FILES:
            hinted.extend(_resolve_repo_file_reference(path, None, full_index, basename_index))

    if _is_scoring_question(question):
        for path in SCORING_METHOD_FILES:
            hinted.extend(_resolve_repo_file_reference(path, None, full_index, basename_index))

    if _is_tableau_export_question(question):
        for path in TABLEAU_EXPORT_FILES:
            hinted.extend(_resolve_repo_file_reference(path, None, full_index, basename_index))

    return _dedupe_paths(hinted)


def _question_priority_paths(question: str, allowed_items: List[Dict[str, Any]]) -> List[str]:
    full_index, basename_index = _allowed_path_indexes(allowed_items)
    priority: List[str] = []

    for mention in _extract_file_mentions(question):
        priority.extend(_resolve_repo_file_reference(mention, None, full_index, basename_index))

    priority.extend(_topic_hint_paths(question, full_index, basename_index))
    return _dedupe_paths(priority)


def _referenced_paths_from_text(
    source_path: str,
    text: str,
    allowed_items: List[Dict[str, Any]],
    keywords: List[str],
    general: bool,
) -> List[str]:
    full_index, basename_index = _allowed_path_indexes(allowed_items)
    references: List[str] = []

    for mention in _extract_file_mentions(text):
        references.extend(_resolve_repo_file_reference(mention, source_path, full_index, basename_index))

    references = [path for path in _dedupe_paths(references) if path.lower() != source_path.lower()]

    def reference_score(path: str) -> int:
        score = _score_path(path, keywords, general)
        lower = path.lower()
        base = lower.rsplit("/", 1)[-1]
        if path in SOURCE_OF_TRUTH_FILES or lower in {p.lower() for p in SOURCE_OF_TRUTH_FILES}:
            score += 18
        # Strongly prefer a referenced methodology file when the question is about methodology.
        if "methodolog" in " ".join(keywords) and "methodology" in lower:
            score += 100
        if "data" in keywords and ("data_sources" in lower or "data_dictionary" in lower):
            score += 60
        if "right-sizing" in lower or "right_sizing" in lower:
            score += 20
        if "electrical" in lower:
            score += 20
        if "tableau" in " ".join(keywords) or "export" in " ".join(keywords):
            if lower in {p.lower() for p in TABLEAU_EXPORT_FILES}:
                score += 90
            if lower.startswith("src/") and any(term in lower for term in ["tableau", "export", "check"]):
                score += 70
        if base == "readme.md":
            score += 8
        return score

    references.sort(key=lambda p: (reference_score(p), -len(p)), reverse=True)
    return references

def _select_repo_context(question: str) -> Tuple[str, List[str], Dict[str, Any]]:
    owner, repo = _repo_owner_repo()
    branch = _repo_branch(owner, repo)
    keywords = _keywords(question)
    general = _is_general_project_question(question)
    scoring_question = _is_scoring_question(question)
    tableau_question = _is_tableau_export_question(question)
    tree = _fetch_repo_tree(owner, repo, branch)

    allowed_items = []
    for item in tree:
        path = str(item.get("path", ""))
        if path and _is_allowed_repo_path(path, item):
            allowed_items.append(item)

    item_by_path = {str(item.get("path", "")).replace("\\", "/").strip("/"): item for item in allowed_items}
    priority_paths = _question_priority_paths(question, allowed_items)
    priority_set = {path.lower() for path in priority_paths}

    # Score paths first. Exact question mentions and topic-hinted source-of-truth docs
    # get a large boost so they cannot be displaced by a generic report/script file.
    path_scored: List[Tuple[int, str, Dict[str, Any]]] = []
    for item in allowed_items:
        path = str(item.get("path", "")).replace("\\", "/").strip("/")
        path_score = _score_path(path, keywords, general)
        lower = path.lower()

        if lower in priority_set:
            path_score += 1000
        if lower in {p.lower() for p in SOURCE_OF_TRUTH_FILES}:
            path_score += 12
        if lower.startswith("docs/") and lower.endswith(".md"):
            path_score += 8

        if path_score > 0 or general or lower in priority_set:
            path_scored.append((path_score, path, item))

    if not path_scored:
        # Fallback for unusual questions: still scan important project files if present.
        fallback_names = {p.lower() for p in SOURCE_OF_TRUTH_FILES} | {"index.html", "dashboard.html", "results.html", "methodology.html"}
        for item in allowed_items:
            path = str(item.get("path", "")).replace("\\", "/").strip("/")
            lower = path.lower()
            base = lower.rsplit("/", 1)[-1]
            if lower in fallback_names or base in fallback_names:
                path_scored.append((_score_path(path, keywords, True) + 20, path, item))

    path_scored.sort(key=lambda x: (x[0], -len(x[1])), reverse=True)

    max_scan = _env_int("MAX_FILES_TO_SCAN", 32, 3, 80)
    max_referenced = _env_int("MAX_REFERENCED_FILES", 4, 0, 12)
    max_file_chars = _env_int("MAX_REPO_FILE_CHARS", 6500, 1200, 20000)
    max_repo_files = _env_int("MAX_REPO_FILES", 6, 1, 12)
    if scoring_question:
        # Scoring answers need room for methodology + dictionary/workflow + implementation files.
        max_repo_files = max(max_repo_files, 6)
    if tableau_question:
        # File-support/export answers should include both the builder/checker scripts and docs.
        max_repo_files = max(max_repo_files, 7)
    max_context_chars = _env_int("MAX_REPO_CONTEXT_CHARS", 22000, 4000, 60000)
    if tableau_question:
        # Leave enough budget for direct script excerpts plus Tableau README/docs.
        max_context_chars = max(max_context_chars, 30000)

    # Build an ordered fetch plan: priority paths first, then the highest-scored paths.
    fetch_plan: List[Tuple[int, str, Dict[str, Any], str]] = []
    for path in priority_paths:
        item = item_by_path.get(path)
        if item:
            fetch_plan.append((2000 + _score_path(path, keywords, general), path, item, "question_priority"))

    for score, path, item in path_scored:
        fetch_plan.append((score, path, item, "path_score"))

    deduped_fetch_plan: List[Tuple[int, str, Dict[str, Any], str]] = []
    seen_fetch = set()
    for score, path, item, reason in sorted(fetch_plan, key=lambda x: (x[0], -len(x[1])), reverse=True):
        key = path.lower()
        if key not in seen_fetch:
            seen_fetch.add(key)
            deduped_fetch_plan.append((score, path, item, reason))
        if len(deduped_fetch_plan) >= max_scan:
            break

    fetched: List[Tuple[int, str, str, str]] = []
    fetched_paths = set()
    fetch_errors: List[str] = []

    for path_score, path, _item, reason in deduped_fetch_plan:
        try:
            raw_text = _fetch_file_text(owner, repo, branch, path)
            clean_text = _normalize_text_for_context(path, raw_text)
            if not clean_text:
                continue
            score = _content_score(path, clean_text, keywords, general, path_score)
            if path.lower() in priority_set:
                score += 1200
            fetched.append((score, path, clean_text, reason))
            fetched_paths.add(path.lower())
        except Exception as exc:
            fetch_errors.append(f"{path}: {str(exc)[:160]}")

    # Mandatory direct-file pass. If the question asks what files support a feature,
    # the strongest source files must be fetched directly when they exist. This avoids
    # answers that name src/build_tableau_exports.py while the Sources checked list only
    # shows README files that mentioned it.
    mandatory_paths: List[str] = []
    if tableau_question:
        mandatory_paths.extend(TABLEAU_EXPORT_FILES)
    if scoring_question:
        mandatory_paths.extend(SCORING_METHOD_FILES[:6])

    for path in _dedupe_paths(mandatory_paths):
        actual_path = item_by_path.get(path) and path
        if not actual_path:
            # Case-insensitive fallback.
            for known in item_by_path.keys():
                if known.lower() == path.lower():
                    actual_path = known
                    break
        if not actual_path or actual_path.lower() in fetched_paths:
            continue
        try:
            raw_text = _fetch_file_text(owner, repo, branch, actual_path)
            clean_text = _normalize_text_for_context(actual_path, raw_text)
            if not clean_text:
                continue
            forced_score = 2600 + _score_path(actual_path, keywords, general)
            fetched.append((forced_score, actual_path, clean_text, "mandatory_direct_source"))
            fetched_paths.add(actual_path.lower())
        except Exception as exc:
            fetch_errors.append(f"{actual_path}: {str(exc)[:160]}")

    # Second pass: if a selected/high-scored file references another relevant source-of-truth
    # document, fetch it too. This fixes cases where docs/README.md names METHODOLOGY.md
    # but the old selector stopped before opening the actual methodology file.
    referenced_candidates: List[str] = []
    for score, path, text, _reason in sorted(fetched, key=lambda x: x[0], reverse=True)[:8]:
        referenced_candidates.extend(_referenced_paths_from_text(path, text, allowed_items, keywords, general))

    referenced_candidates = [p for p in _dedupe_paths(referenced_candidates) if p.lower() not in fetched_paths]

    referenced_added: List[str] = []
    for path in referenced_candidates[:max_referenced]:
        item = item_by_path.get(path)
        if not item:
            continue
        try:
            raw_text = _fetch_file_text(owner, repo, branch, path)
            clean_text = _normalize_text_for_context(path, raw_text)
            if not clean_text:
                continue
            path_score = _score_path(path, keywords, general) + 450
            if path.lower() in {p.lower() for p in SOURCE_OF_TRUTH_FILES}:
                path_score += 80
            score = _content_score(path, clean_text, keywords, general, path_score)
            fetched.append((score, path, clean_text, "referenced_by_selected_file"))
            fetched_paths.add(path.lower())
            referenced_added.append(path)
        except Exception as exc:
            fetch_errors.append(f"{path}: {str(exc)[:160]}")

    fetched.sort(key=lambda x: x[0], reverse=True)
    selected = [item for item in fetched if item[0] > 0][:max_repo_files]

    if not selected and fetched:
        selected = fetched[:min(max_repo_files, 3)]

    if general and selected:
        overview_rank = {p.lower(): i for i, p in enumerate(BROAD_OVERVIEW_FILES)}
        overview_selected = sorted(
            [item for item in selected if item[1].lower() in overview_rank],
            key=lambda item: overview_rank[item[1].lower()],
        )
        other_selected = [item for item in selected if item[1].lower() not in overview_rank]
        selected = (overview_selected + other_selected)[:max_repo_files]

    if scoring_question and fetched:
        scoring_rank = {p.lower(): i for i, p in enumerate(SCORING_METHOD_FILES)}
        forced_scoring = sorted(
            [item for item in fetched if item[1].lower() in scoring_rank],
            key=lambda item: scoring_rank[item[1].lower()],
        )
        already = {item[1].lower() for item in forced_scoring}
        remaining_selected = [item for item in selected if item[1].lower() not in already]
        selected = (forced_scoring + remaining_selected)[:max_repo_files]

    if tableau_question and fetched:
        tableau_rank = {p.lower(): i for i, p in enumerate(TABLEAU_EXPORT_FILES)}
        forced_tableau = sorted(
            [item for item in fetched if item[1].lower() in tableau_rank],
            key=lambda item: tableau_rank[item[1].lower()],
        )
        already = {item[1].lower() for item in forced_tableau}
        remaining_selected = [item for item in selected if item[1].lower() not in already]
        selected = (forced_tableau + remaining_selected)[:max_repo_files]

    chunks: List[str] = []
    sources: List[str] = []
    chars_used = 0

    for _score, path, text, reason in selected:
        remaining = max_context_chars - chars_used
        if remaining <= 800:
            break
        per_file = min(max_file_chars, max(800, remaining))
        excerpt = _excerpt_text(text, keywords, per_file)
        source_block = f"SOURCE FILE: {path}\nSELECTION REASON: {reason}\nEXCERPT:\n{excerpt}\n"
        if chars_used + len(source_block) > max_context_chars:
            source_block = source_block[: max_context_chars - chars_used]
        chunks.append(source_block)
        sources.append(path)
        chars_used += len(source_block)

    context = "\n---\n".join(chunks)
    debug = {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "allowedFileCount": len(allowed_items),
        "candidateCount": len(path_scored),
        "fetchedCount": len(fetched),
        "selectedCount": len(sources),
        "keywords": keywords,
        "generalProjectQuestion": general,
        "scoringQuestion": scoring_question,
        "tableauExportQuestion": tableau_question,
        "scoringMethodFiles": SCORING_METHOD_FILES if scoring_question else [],
        "tableauExportFiles": TABLEAU_EXPORT_FILES if tableau_question else [],
        "broadOverviewFiles": BROAD_OVERVIEW_FILES if general else [],
        "priorityPaths": priority_paths,
        "referencedAdded": referenced_added,
        "fetchErrorCount": len(fetch_errors),
        "fetchErrorsSample": fetch_errors[:3],
    }
    return context, sources, debug


def _extract_output_text(openai_payload: Dict[str, Any]) -> str:
    direct = openai_payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    chunks: List[str] = []
    for item in openai_payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())

    if chunks:
        return "\n\n".join(chunks).strip()

    return "I could not generate a response for that request."


def _postprocess_answer_quality(answer: str) -> str:
    """Lightweight production guardrail for incomplete model endings.

    The prompt should prevent unfinished formulas, but this final pass catches
    common truncation/formatting cases such as:
      public_access = 0 -> readiness_access_adjustment =
    and converts them into a safe non-hallucinated placeholder.
    """
    if not isinstance(answer, str):
        return "I could not generate a complete response for that request."

    text = answer.strip()
    if not text:
        return "I could not generate a complete response for that request."

    lines = text.splitlines()
    changed = False
    fixed_lines: List[str] = []

    for line in lines:
        stripped = line.rstrip()
        # Fix equations or mappings that end with no right-hand value.
        if re.search(r"(?:=|->|→)\s*$", stripped):
            stripped = stripped + " not confirmed in the selected sources"
            changed = True
        # Fix an empty markdown bullet/numbered item.
        elif re.match(r"^\s*(?:[-*+]\s*|\d+[.)]\s*)$", stripped):
            stripped = re.sub(r"\s*$", "not confirmed in the selected sources", stripped)
            changed = True
        fixed_lines.append(stripped)

    text = "\n".join(fixed_lines).strip()

    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    if nonempty:
        last = nonempty[-1]
        # Catch a final dangling colon/bullet/operator. Avoid false positives for normal sentences.
        if re.search(r"(?:=|->|→|[+*/-])\s*$", last) or re.match(r"^(?:[-*+]\s*|\d+[.)]\s*)$", last):
            text += "\n\nNote: The selected sources did not provide enough confirmed detail to complete the unfinished item above."
            changed = True
        elif last.endswith(":") and len(text) > 350:
            text += "\n\nNote: The selected sources did not provide enough confirmed detail to complete that final section."
            changed = True

    # Do not leave a final section whose only content is an unsupported placeholder.
    cleaned = re.sub(
        r"\n?\s*\d+[.)]\s+[^\n]+\n\s*-?\s*not confirmed in the selected sources\.?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    if cleaned != text:
        text = cleaned
        changed = True

    # Improve awkward placeholder bullets such as "-not confirmed..." if one remains.
    cleaned = re.sub(r"(?m)^\s*-\s*not confirmed in the selected sources\.?\s*$", "- not confirmed in the selected sources", text, flags=re.IGNORECASE)
    if cleaned != text:
        text = cleaned
        changed = True

    # If the model calls two differently named adjustment fields inconsistent, soften it.
    cleaned = text.replace(
        "The selected excerpt shows two values, but they are inconsistent and not fully explained:",
        "The selected excerpts show two related adjustment fields. They may be separate fields, and their relationship is not fully explained:"
    ).replace(
        "The selected excerpts show two values, but they are inconsistent and not fully explained:",
        "The selected excerpts show two related adjustment fields. They may be separate fields, and their relationship is not fully explained:"
    )
    if cleaned != text:
        text = cleaned
        changed = True

    # Remove or repair a trailing fragment that is likely caused by output cutoff,
    # e.g. a final orphan line like "public" after a public_access mapping list.
    lines2 = text.splitlines()
    while lines2 and not lines2[-1].strip():
        lines2.pop()
    if lines2:
        last_line = lines2[-1].strip()
        previous_text = "\n".join(lines2[:-1]).lower()
        looks_like_orphan_word = bool(re.match(r"^[A-Za-z_][A-Za-z0-9_ -]{2,45}$", last_line)) and not re.search(r"[.!?:;)]$", last_line)
        scoring_or_access_context = any(term in previous_text[-900:] for term in [
            "access_adjustment", "readiness_access_adjustment", "public_access", "readiness_score", "subscore"
        ])
        if looks_like_orphan_word and scoring_or_access_context:
            lines2 = lines2[:-1]
            text = "\n".join(lines2).rstrip()
            if "public_access" in previous_text[-900:] and "not confirmed in the selected sources" not in text.lower()[-500:]:
                text += "\n\nThe remaining public-access adjustment detail is not confirmed in the selected sources."
            else:
                text += "\n\nOne unfinished trailing fragment was removed because the selected sources did not confirm the remaining detail."
            changed = True

    # If a markdown code fence was opened but not closed, close it to prevent broken rendering.
    if text.count("```") % 2 == 1:
        text += "\n```"
        changed = True

    if changed:
        print(json.dumps({"event": "answer_quality_guard_applied"}))

    return text



def _postprocess_source_answer_consistency(answer: str, sources: List[str]) -> str:
    """Light cleanup to avoid direct-inspection wording for files not in sources.

    The main fix is source selection, but this guard catches cases where the model
    mentions a repo file that was not actually selected.
    """
    if not isinstance(answer, str):
        return answer
    source_set = {s.lower() for s in (sources or [])}
    mentions = _extract_file_mentions(answer)
    unchecked = [m for m in mentions if m.lower() not in source_set]
    if not unchecked:
        return answer

    # For production UX, do not add a noisy warning for every incidental output
    # filename. Add one concise caveat only for source/code files the answer might
    # imply were directly inspected.
    repo_source_unchecked = [m for m in unchecked if m.lower().startswith(("src/", "docs/", "tableau/", "data/"))]
    if repo_source_unchecked:
        joined = ", ".join(repo_source_unchecked[:4])
        note = f"Note: {joined} were mentioned in the answer or selected docs, but they were not directly included in this response's Sources checked list."
        if note not in answer:
            answer = answer.rstrip() + "\n\n" + note
    return answer


def _build_model_input(message: str, repo_context: str, sources: List[str], repo_debug: Dict[str, Any], history: Optional[List[Dict[str, str]]] = None) -> str:
    history = history or []
    history_text = _history_text_for_prompt(history)
    followup_note = ""
    if history and _is_short_followup(message):
        followup_note = "\nThe current user message is a short follow-up. Use the recent conversation context to resolve what 'that' or 'it' refers to. Answer the prior offered follow-up directly.\n"

    history_block = ""
    if history_text:
        history_block = f"""Recent conversation context, newest turns last:
{history_text}

"""

    if repo_context.strip():
        quality_note = ""
        if repo_debug.get("scoringQuestion"):
            quality_note = "\nThis appears to be a scoring-method question. Use compact mode: answer in at most 7 short numbered sections and about 650 words. Do not add a section whose only content would be not-confirmed. Distinguish equity scoring from public-access adjustment. If access_adjustment and readiness_access_adjustment both appear, explain that they are separate named fields unless the excerpts explicitly say they conflict. For public-access values, list only fully visible confirmed mappings; if a mapping is incomplete, say the remaining value is not confirmed instead of starting an unfinished line. End with a complete sentence.\n"
        if repo_debug.get("tableauExportQuestion"):
            quality_note += "\nThis appears to be a Tableau/export file-support question. Only say a file directly supports Tableau exports if it is listed in Repository files checked. If a file is merely mentioned by another selected doc, say it is referenced by the selected docs instead of implying direct inspection. Prefer direct source alignment over a longer answer.\n"
        return f"""{history_block}Current user question:
{message}
{followup_note}
Repository files checked:
{json.dumps(sources, indent=2)}

Relevant repository excerpts:
{repo_context}
{quality_note}
Answer the current user question using the repository excerpts above and the recent conversation context when needed. If the excerpts are incomplete, say what is missing. Do not invent file contents or unsupported project facts. Prefer a complete concise answer over a long answer that may be cut off."""

    return f"""{history_block}Current user question:
{message}
{followup_note}
No relevant repository file excerpts were found or loaded for this question.
Repository search debug summary:
{json.dumps({k: repo_debug.get(k) for k in ['owner', 'repo', 'branch', 'allowedFileCount', 'candidateCount', 'fetchedCount', 'selectedCount']}, indent=2)}

Answer only at a high level using the general project context. Clearly say that no relevant repository files were checked for this response."""


def _call_openai(message: str, session_id: str, user: Dict[str, str], repo_context: str, sources: List[str], repo_debug: Dict[str, Any], history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, Dict[str, Any]]:
    api_key = _secret_or_env("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to Secrets Manager or Lambda environment variables.")

    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    max_output_tokens = _env_int("MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS, 100, 2000)
    model_input = _build_model_input(message, repo_context, sources, repo_debug, history)

    request_payload = {
        "model": model,
        "instructions": REPO_AWARE_INSTRUCTIONS + "\n\n" + PROJECT_BASE_CONTEXT,
        "input": [
            {
                "role": "user",
                "content": model_input,
            }
        ],
        "max_output_tokens": max_output_tokens,
        "store": False,
        "metadata": {
            "project": "future-city-fellowship",
            "phase": "phase_5m_direct_file_source_alignment",
            "session_id": session_id[:64],
            "user_sub": user.get("sub", "unknown-user")[:96],
            "source_count": str(len(sources)),
        },
    }

    encoded_body = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=encoded_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            response_body = response.read().decode("utf-8")
            response_payload = json.loads(response_body)
            return _extract_output_text(response_payload), (response_payload.get("usage") or {})
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        safe_message = f"OpenAI API request failed with status {exc.code}."
        try:
            error_payload = json.loads(error_body)
            api_error = error_payload.get("error", {})
            if isinstance(api_error, dict) and api_error.get("message"):
                safe_message += f" {api_error.get('message')}"
        except Exception:
            pass
        raise RuntimeError(safe_message) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach the OpenAI API from Lambda.") from exc


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = _method_from_event(event)

    if method == "OPTIONS":
        return _json_response(200, {"ok": True}, event)

    if method != "POST":
        return _json_response(
            405,
            {
                "ok": False,
                "answer": "Method not allowed. Use POST /chat.",
                "sources": [],
            },
            event,
        )

    claims = _auth_claims(event)
    # Public access: no sign-in is required. A signed-in caller (if a token is ever sent and
    # verified upstream) keeps their identity; everyone else is an anonymous visitor keyed by a
    # salted hash of their source IP, used only for rate limiting. The raw IP is never stored.
    user = _user_from_claims(claims) if claims else _anonymous_user(event)

    try:
        body = _parse_body(event)
    except Exception:
        return _json_response(
            400,
            {
                "ok": False,
                "answer": "Invalid request body. Send JSON with a message field.",
                "sources": [],
            },
            event,
        )

    message = str(body.get("message", "")).strip()
    session_id = str(body.get("sessionId", "anonymous-session")).strip() or "anonymous-session"
    history = _sanitize_history(body.get("history", []))
    selection_query = _contextual_selection_query(message, history)
    max_message_length = _env_int("MAX_MESSAGE_LENGTH", DEFAULT_MAX_MESSAGE_LENGTH, 200, 8000)

    if not message:
        return _json_response(
            400,
            {
                "ok": False,
                "answer": "Please send a non-empty message.",
                "sources": [],
            },
            event,
        )

    if len(message) > max_message_length:
        return _json_response(
            413,
            {
                "ok": False,
                "answer": f"Please keep your message under {max_message_length} characters.",
                "sources": [],
            },
            event,
        )

    start = time.time()
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    rate_check = _check_rate_limits(user)
    if not rate_check.get("allowed", True):
        latency_ms = int((time.time() - start) * 1000)
        _log_usage_event(
            status="rate_limited",
            user=user,
            session_id=session_id,
            message=message,
            model=model,
            sources=[],
            latency_ms=latency_ms,
            repo_debug={"rateLimit": rate_check},
            error=rate_check.get("answer"),
        )
        return _json_response(
            429,
            {
                "ok": False,
                "answer": rate_check.get("answer", "Assistant usage limit reached. Please try again later."),
                "sources": [],
                "phase": "phase_5m_direct_file_source_alignment",
                "rateLimit": {k: v for k, v in rate_check.items() if k != "answer"},
            },
            event,
        )

    repo_context = ""
    sources: List[str] = []
    repo_debug: Dict[str, Any] = {}
    repo_error: Optional[str] = None
    openai_usage: Dict[str, Any] = {}

    try:
        repo_context, sources, repo_debug = _select_repo_context(selection_query)
    except Exception as exc:
        repo_error = str(exc)
        repo_debug = {"error": repo_error[:300]}
        print(json.dumps({
            "event": "phase_4_repo_lookup_error",
            "error": repo_error,
            "userSub": user.get("sub"),
            "userEmail": user.get("email"),
            "sessionId": session_id[:64],
            "messageLength": len(message),
        }))

    try:
        answer, openai_usage = _call_openai(message, session_id, user, repo_context, sources, repo_debug, history)
        answer = _postprocess_answer_quality(answer)
        answer = _postprocess_source_answer_consistency(answer, sources)
        if repo_error and not sources:
            answer = "I could not access the GitHub repository for this response, so this answer is high-level only.\n\n" + answer
    except Exception as exc:
        print(json.dumps({
            "event": "phase_5_model_error",
            "error": str(exc),
            "userSub": user.get("sub"),
            "userEmail": user.get("email"),
            "sessionId": session_id[:64],
            "messageLength": len(message),
            "model": model,
            "sources": sources,
            "repoDebug": repo_debug,
        }))
        _log_usage_event(
            status="model_error",
            user=user,
            session_id=session_id,
            message=message,
            model=model,
            sources=sources,
            latency_ms=int((time.time() - start) * 1000),
            repo_debug=repo_debug,
            usage=openai_usage,
            error=str(exc),
        )
        return _json_response(
            502,
            {
                "ok": False,
                "answer": "The AI model or repository-aware response failed. Check Lambda logs and configuration.",
                "sources": sources,
                "phase": "phase_5m_direct_file_source_alignment",
            },
            event,
        )

    latency_ms = int((time.time() - start) * 1000)

    _log_usage_event(
        status="success",
        user=user,
        session_id=session_id,
        message=message,
        model=model,
        sources=sources,
        latency_ms=latency_ms,
        repo_debug=repo_debug,
        usage=openai_usage,
    )

    print(json.dumps({
        "event": "assistant_message",
        "phase": "phase_5m_direct_file_source_alignment",
        "userSub": user.get("sub"),
        "userEmail": user.get("email"),
        "sessionId": session_id[:64],
        "messageLength": len(message),
        "model": model,
        "latencyMs": latency_ms,
        "sources": sources,
        "repoDebug": repo_debug,
        "openaiUsage": openai_usage,
        "rateLimit": rate_check,
    }))

    return _json_response(
        200,
        {
            "ok": True,
            "answer": answer,
            "sources": sources,
            "phase": "phase_5m_direct_file_source_alignment",
            "model": model,
            "latencyMs": latency_ms,
            "sessionId": session_id,
            "usage": openai_usage,
            "rateLimit": {k: v for k, v in rate_check.items() if k != "answer"},
            "repo": {
                "owner": repo_debug.get("owner"),
                "name": repo_debug.get("repo"),
                "branch": repo_debug.get("branch"),
                "selectedCount": len(sources),
            },
        },
        event,
    )
