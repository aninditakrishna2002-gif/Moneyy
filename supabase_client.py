"""
supabase_client.py - Supabase Client & Authentication Helper for MONEYY
Safely manages Supabase initialization, user auth, and JWT session handling.
Strictly protects the SUPABASE_SECRET_KEY server-side.
"""

import os
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file if present
load_dotenv()

# Read Environment Variables with fallbacks
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip()
SUPABASE_PUBLISHABLE_KEY = (
    os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
    or ""
).strip()
SUPABASE_SECRET_KEY = (
    os.environ.get("SUPABASE_SECRET_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or ""
).strip()


def is_supabase_configured() -> bool:
    """Returns True if the required Supabase credentials are provided."""
    return bool(SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY)


def get_anon_client() -> Client:
    """
    Returns a Supabase client using the Publishable / Anon key.
    Used for public authentication actions (sign up, sign in).
    """
    if not is_supabase_configured():
        raise RuntimeError(
            "Supabase is not configured. Please set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY."
        )
    return create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)


def get_admin_client() -> Client:
    """
    Returns a Supabase client using the Secret Service Role key.
    SECURITY NOTICE: This client bypasses RLS and MUST ONLY be used on the server.
    Never expose its results or keys to the frontend or GitHub.
    """
    key = SUPABASE_SECRET_KEY or SUPABASE_PUBLISHABLE_KEY
    if not SUPABASE_URL or not key:
        raise RuntimeError("Supabase Admin key or URL is not configured.")
    return create_client(SUPABASE_URL, key)


def get_user_client(access_token: str) -> Client:
    """
    Returns an authenticated Supabase client scoped to the user's JWT.
    This client automatically enforces Row Level Security (RLS) policies:
    auth.uid() is matched directly to the user in PostgreSQL.
    """
    client = get_anon_client()
    if access_token:
        client.postgrest.auth(access_token)
    return client


# ==============================================================================
# AUTHENTICATION FUNCTIONS
# ==============================================================================

def sign_up_user(email: str, password: str, name: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Registers a new user in Supabase Auth with their name in user_metadata.
    Returns (success: bool, result: dict).
    """
    try:
        client = get_anon_client()
        credentials = {
            "email": email.strip().lower(),
            "password": password,
            "options": {
                "data": {
                    "name": name.strip(),
                    "full_name": name.strip(),
                }
            },
        }
        res = client.auth.sign_up(credentials)
        if not res.user:
            return False, {"error": "Signup failed. Please try again."}

        # Format user response
        user_data = {
            "id": res.user.id,
            "email": res.user.email,
            "name": res.user.user_metadata.get("name") if res.user.user_metadata else name.strip(),
        }

        # If Supabase email confirmation is disabled, session & access_token are returned immediately
        session_data = {}
        if res.session:
            session_data = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
                "expires_at": res.session.expires_at,
            }

        return True, {
            "user": user_data,
            "session": session_data,
            "message": "Signup successful!",
        }
    except Exception as e:
        err_msg = str(e)
        if "already registered" in err_msg.lower() or "already exists" in err_msg.lower():
            err_msg = "An account with this email already exists. Please log in."
        elif "password" in err_msg.lower() and "short" in err_msg.lower():
            err_msg = "Password should be at least 6 characters long."
        return False, {"error": err_msg}


def sign_in_user(email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Authenticates an existing user via Supabase Auth.
    Returns (success: bool, result: dict) containing user profile and JWT session token.
    """
    try:
        client = get_anon_client()
        res = client.auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password,
        })
        if not res.user or not res.session:
            return False, {"error": "Invalid email or password."}

        user_name = "Student"
        if res.user.user_metadata and "name" in res.user.user_metadata:
            user_name = res.user.user_metadata["name"]

        user_data = {
            "id": res.user.id,
            "email": res.user.email,
            "name": user_name,
        }
        session_data = {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "expires_at": res.session.expires_at,
        }
        return True, {
            "user": user_data,
            "session": session_data,
            "message": "Login successful!",
        }
    except Exception as e:
        err_msg = str(e)
        if "invalid" in err_msg.lower() or "credentials" in err_msg.lower():
            err_msg = "Invalid email or password. Please check your credentials."
        return False, {"error": err_msg}


def get_user_from_token(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies the user's JWT access token with Supabase and returns the user object.
    Returns None if the token is invalid or expired.
    """
    if not access_token:
        return None
    try:
        client = get_anon_client()
        res = client.auth.get_user(access_token)
        if not res or not res.user:
            return None
        user = res.user
        name = "Student"
        if user.user_metadata and "name" in user.user_metadata:
            name = user.user_metadata["name"]
        return {
            "id": user.id,
            "email": user.email,
            "name": name,
        }
    except Exception:
        return None


def sign_out_user(access_token: str) -> bool:
    """Signs out user from Supabase."""
    try:
        client = get_user_client(access_token)
        client.auth.sign_out()
        return True
    except Exception:
        return False
