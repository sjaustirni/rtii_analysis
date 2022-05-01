import os
from supabase import create_client, Client


def download_data_for(usernames):
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    return supabase.table("experiment_logs"). \
        select("*"). \
        filter("participant", "in", usernames). \
        execute()
