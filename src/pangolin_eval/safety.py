from __future__ import annotations

from urllib.parse import urlparse

SAFE_API_KEY_ENV_NAMES = {
    "OPENAI_API_KEY",
    "LITELLM_API_KEY",
    "OLLAMA_API_KEY",
    "VLLM_API_KEY",
}
SAFE_API_KEY_ENV_PREFIXES = ("PANGOLIN_EVAL_",)
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
SAFE_API_KEY_ENV_HOSTS = {
    "LITELLM_API_KEY": set(),
    "OLLAMA_API_KEY": set(),
    "OPENAI_API_KEY": {"api.openai.com"},
    "VLLM_API_KEY": set(),
}


def validate_openai_connection_security(
    *,
    base_url: str,
    api_key_env: str,
    owner: str,
    allow_unsafe_api_key_env: bool = False,
) -> None:
    hostname = _validate_base_url(base_url, owner)
    _validate_api_key_env(api_key_env, owner, allow_unsafe_api_key_env)
    _validate_api_key_env_host(
        api_key_env,
        hostname,
        owner,
        allow_unsafe_api_key_env,
    )


def _validate_base_url(base_url: str, owner: str) -> str:
    parsed = urlparse(base_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not hostname:
        raise ValueError(f"{owner} field 'base_url' must be an absolute HTTP(S) URL.")
    if parsed.scheme == "http" and hostname not in LOOPBACK_HOSTS:
        raise ValueError(
            f"{owner} field 'base_url' must use HTTPS unless it points to loopback."
        )
    return hostname


def _validate_api_key_env(
    api_key_env: str,
    owner: str,
    allow_unsafe_api_key_env: bool,
) -> None:
    if allow_unsafe_api_key_env:
        return
    if api_key_env in SAFE_API_KEY_ENV_NAMES:
        return
    if any(api_key_env.startswith(prefix) for prefix in SAFE_API_KEY_ENV_PREFIXES):
        return
    allowed = ", ".join(sorted(SAFE_API_KEY_ENV_NAMES))
    prefixes = ", ".join(SAFE_API_KEY_ENV_PREFIXES)
    raise ValueError(
        f"{owner} field 'api_key_env' must be one of {allowed}, start with "
        f"{prefixes}, or set allow_unsafe_api_key_env to true."
    )


def _validate_api_key_env_host(
    api_key_env: str,
    hostname: str,
    owner: str,
    allow_unsafe_api_key_env: bool,
) -> None:
    if allow_unsafe_api_key_env:
        return
    if hostname in LOOPBACK_HOSTS:
        return
    if any(api_key_env.startswith(prefix) for prefix in SAFE_API_KEY_ENV_PREFIXES):
        return
    allowed_hosts = SAFE_API_KEY_ENV_HOSTS.get(api_key_env)
    if allowed_hosts is None:
        return
    if hostname in allowed_hosts:
        return
    hosts = ", ".join(sorted(allowed_hosts)) or "loopback hosts"
    raise ValueError(
        f"{owner} field 'api_key_env' {api_key_env} may only be sent to {hosts}; "
        "set allow_unsafe_api_key_env to true for trusted custom hosts."
    )
