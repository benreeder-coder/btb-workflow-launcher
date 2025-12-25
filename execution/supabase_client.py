"""
Supabase client singleton for Client Hub.
Provides a single shared connection to Supabase across the application.
"""
import os
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client


class SupabaseClientError(Exception):
    """Raised when Supabase client cannot be initialized."""
    pass


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get or create a Supabase client singleton.

    Environment variables required:
        SUPABASE_URL: Your Supabase project URL
        SUPABASE_KEY: Your Supabase service role key (for server-side operations)

    Returns:
        Supabase Client instance

    Raises:
        SupabaseClientError: If environment variables are missing
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        raise SupabaseClientError(
            "SUPABASE_URL environment variable is not set. "
            "Please add it to your .env file or Railway environment variables."
        )

    if not supabase_key:
        raise SupabaseClientError(
            "SUPABASE_KEY environment variable is not set. "
            "Please add it to your .env file or Railway environment variables."
        )

    try:
        client = create_client(supabase_url, supabase_key)
        return client
    except Exception as e:
        raise SupabaseClientError(f"Failed to create Supabase client: {e}")


def get_supabase() -> Client:
    """
    Convenience function to get the Supabase client.
    Use this in FastAPI dependencies.
    """
    return get_supabase_client()


# Optional: Health check function
def check_supabase_connection() -> bool:
    """
    Check if Supabase connection is working.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        client = get_supabase_client()
        # Try a simple query to verify connection
        result = client.table("settings").select("id").limit(1).execute()
        return True
    except Exception:
        return False
