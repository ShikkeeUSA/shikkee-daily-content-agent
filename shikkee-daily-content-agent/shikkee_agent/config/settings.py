"""
Central config. Values that are genuinely secret (API keys, tokens, app passwords)
are read from environment variables only -- never hardcode them here.
Values that are just identifiers (Airtable base/table IDs, Metricool blog IDs,
HeyGen avatar/voice IDs) are safe to default here since they are specific to how
Shikkee's own accounts are wired up, not credentials.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass
class Settings:
    # Airtable
    airtable_api_key: str = field(default_factory=lambda: _env("AIRTABLE_API_KEY"))
    airtable_base_id: str = field(default_factory=lambda: _env("AIRTABLE_BASE_ID", "appUOOmy5OXyCLkJW"))
    airtable_content_table_id: str = field(default_factory=lambda: _env("AIRTABLE_CONTENT_TABLE_ID", "tblYlLTqk7Yu3oSyF"))
    airtable_rss_table_id: str = field(default_factory=lambda: _env("AIRTABLE_RSS_TABLE_ID", "tblEGT10NV9aS5lE1"))

    # Metricool
    metricool_user_token: str = field(default_factory=lambda: _env("METRICOOL_USER_TOKEN"))
    metricool_user_id: str = field(default_factory=lambda: _env("METRICOOL_USER_ID"))
    blog_shikkee_usa: str = field(default_factory=lambda: _env("METRICOOL_BLOG_SHIKKEE_USA", "5177872"))
    blog_tal_personal: str = field(default_factory=lambda: _env("METRICOOL_BLOG_TAL_PERSONAL", "5983065"))
    blog_ayala_profile: str = field(default_factory=lambda: _env("METRICOOL_BLOG_AYALA_PROFILE", "6104436"))

    # WordPress
    wp_base_url: str = field(default_factory=lambda: _env("WORDPRESS_BASE_URL", "https://shikkee.com"))
    wp_username: str = field(default_factory=lambda: _env("WORDPRESS_USERNAME"))
    wp_app_password: str = field(default_factory=lambda: _env("WORDPRESS_APP_PASSWORD"))

    # HeyGen
    heygen_api_key: str = field(default_factory=lambda: _env("HEYGEN_API_KEY"))
    heygen_brand_kit_id: str = field(default_factory=lambda: _env("HEYGEN_BRAND_KIT_ID", "692bee1619c34f409d10e97a5cec8b60"))

    # Slack
    slack_bot_token: str = field(default_factory=lambda: _env("SLACK_BOT_TOKEN"))
    slack_narrative_channel_id: str = field(default_factory=lambda: _env("SLACK_NARRATIVE_CHANNEL_ID", "C0BM7DT2UUC"))

    # Google Drive
    gdrive_asset_root_folder_id: str = field(default_factory=lambda: _env("GDRIVE_ASSET_ROOT_FOLDER_ID", "1cA6PjKkuSOgqPrLd-nSKeZ94f15DRUTb"))

    # Browser automation
    playwright_state_dir: str = field(default_factory=lambda: _env("PLAYWRIGHT_STATE_DIR", "./.browser_state"))

    # Misc
    timezone_shikkee_usa: str = "America/Chicago"
    timezone_founders: str = "America/New_York"
