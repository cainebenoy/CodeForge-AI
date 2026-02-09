"""
Supabase client for database operations
Uses service role key for backend operations
"""
from supabase import create_client, Client

from app.core.config import settings

# Service role client - has elevated permissions
# SECURITY: Never expose this to the client
supabase_client: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
)
