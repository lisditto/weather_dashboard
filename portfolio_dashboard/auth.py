"""OAuth 2.0 social login — Naver and Kakao.

Flow:
  1. Call naver_login_url() / kakao_login_url() to build the provider URL.
  2. Render an <a href="..." target="_self"> link so the browser navigates
     in the same tab (required for the OAuth redirect to return here).
  3. Provider redirects back to REDIRECT_URI with ?code=...&state=<provider>_...
  4. On next Streamlit load handle_callback() detects the code, exchanges it
     for a token, fetches the user profile, and stores it in session_state.

Secrets required in .streamlit/secrets.toml (or Streamlit Cloud secrets):
  REDIRECT_URI        = "https://your-app.streamlit.app"
  NAVER_CLIENT_ID     = "..."
  NAVER_CLIENT_SECRET = "..."
  KAKAO_CLIENT_ID     = "..."   # REST API key
"""
from __future__ import annotations

import secrets
import urllib.parse

import requests
import streamlit as st

_NAVER_AUTH = "https://nid.naver.com/oauth2.0/authorize"
_NAVER_TOKEN = "https://nid.naver.com/oauth2.0/token"
_NAVER_PROFILE = "https://openapi.naver.com/v1/nid/me"

_KAKAO_AUTH = "https://kauth.kakao.com/oauth/authorize"
_KAKAO_TOKEN = "https://kauth.kakao.com/oauth/token"
_KAKAO_PROFILE = "https://kapi.kakao.com/v2/user/me"


def _redirect_uri() -> str:
    try:
        return st.secrets["REDIRECT_URI"]
    except Exception:
        return "http://localhost:8501"


def _secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except Exception:
        return None


def has_naver() -> bool:
    return bool(_secret("NAVER_CLIENT_ID"))


def has_kakao() -> bool:
    return bool(_secret("KAKAO_CLIENT_ID"))


def naver_login_url() -> str:
    state = "naver_" + secrets.token_urlsafe(12)
    return _NAVER_AUTH + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": _secret("NAVER_CLIENT_ID"),
        "redirect_uri": _redirect_uri(),
        "state": state,
    })


def kakao_login_url() -> str:
    state = "kakao_" + secrets.token_urlsafe(12)
    return _KAKAO_AUTH + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": _secret("KAKAO_CLIENT_ID"),
        "redirect_uri": _redirect_uri(),
        "state": state,
    })


def handle_callback() -> bool:
    """Detect and process OAuth callback. Returns True on successful login."""
    code = st.query_params.get("code")
    state = st.query_params.get("state", "")
    if not code:
        return False

    provider = state.split("_")[0] if "_" in state else ""
    try:
        if provider == "naver":
            user = _fetch_naver_user(code)
        elif provider == "kakao":
            user = _fetch_kakao_user(code)
        else:
            st.error("알 수 없는 로그인 제공자입니다. 다시 시도해 주세요.")
            st.query_params.clear()
            return False

        st.session_state["user"] = user
        st.query_params.clear()
        return True
    except Exception as exc:
        st.error(f"로그인 처리 중 오류가 발생했습니다: {exc}")
        st.query_params.clear()
        return False


def _fetch_naver_user(code: str) -> dict:
    r = requests.post(_NAVER_TOKEN, params={
        "grant_type": "authorization_code",
        "client_id": _secret("NAVER_CLIENT_ID"),
        "client_secret": _secret("NAVER_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": _redirect_uri(),
    }, timeout=10)
    r.raise_for_status()
    token = r.json()["access_token"]

    p = requests.get(_NAVER_PROFILE, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    p.raise_for_status()
    info = p.json()["response"]
    return {
        "provider": "naver",
        "id": info["id"],
        "name": info.get("name") or info.get("nickname", "사용자"),
        "email": info.get("email", ""),
    }


def _fetch_kakao_user(code: str) -> dict:
    r = requests.post(_KAKAO_TOKEN, data={
        "grant_type": "authorization_code",
        "client_id": _secret("KAKAO_CLIENT_ID"),
        "redirect_uri": _redirect_uri(),
        "code": code,
    }, timeout=10)
    r.raise_for_status()
    token = r.json()["access_token"]

    p = requests.get(_KAKAO_PROFILE, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    p.raise_for_status()
    info = p.json()
    account = info.get("kakao_account", {})
    profile = account.get("profile", {})
    return {
        "provider": "kakao",
        "id": str(info["id"]),
        "name": profile.get("nickname", "사용자"),
        "email": account.get("email", ""),
    }


def is_logged_in() -> bool:
    return "user" in st.session_state


def current_user() -> dict | None:
    return st.session_state.get("user")


def logout() -> None:
    st.session_state.pop("user", None)
