"""
The daily six-channel news-to-content pipeline: Instagram, X, LinkedIn, Google
Business Profile, Blog, YouTube. One angle, platform-native copy per channel,
scheduled as drafts (Metricool draft / WordPress draft), logged to Airtable
with status "draft".

LINKEDIN & X MEDIA RULE (2026-09-06, per Tal): X and LinkedIn never carry the
HeyGen avatar video -- only Instagram and YouTube do. X/LinkedIn get a custom
static picture or no image at all. See schedule_six_channel()'s docstring.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.clients.heygen_client import HeyGenClient
from shikkee_agent.clients.metricool_client import MetricoolClient
from shikkee_agent.clients.wordpress_client import WordPressClient
from shikkee_agent.config import settings
from shikkee_agent.config.avatars import ELLA
from shikkee_agent.config.brand_rules import CURRENT_CAMPAIGN_FACTS
from shikkee_agent.pipeline.validators import enforce_or_raise

CHANNELS = ("instagram", "x", "linkedin", "gbp", "blog", "youtube")


@dataclass
class ChannelCopy:
    instagram: str
    x: str
    linkedin: str
    gbp: str
    youtube_title: str
    youtube_description: str
    blog_title: str
    blog_slug: str
    blog_html: str
    blog_excerpt: str
    blog_meta_title: str
    blog_meta_description: str
    blog_focus_keyword: str


def validate_all(copy: ChannelCopy) -> None:
    for field_name in ("instagram", "x", "linkedin", "gbp", "youtube_description", "blog_html"):
        enforce_or_raise(getattr(copy, field_name), context=field_name)


def schedule_six_channel(
    copy: ChannelCopy,
    video_script: str,
    real_asset_url: str,
    blog_category_ids: list[int],
    blog_tag_ids: list[int],
    blog_featured_media_id: int,
    publish_hour_local: int = 15,
    x_linkedin_image_url: str | None = None,
) -> dict:
    """Generates one Ella video for Instagram/YouTube, schedules all five social
    posts as Metricool drafts, and creates the WordPress blog draft with SEO/AEO
    metadata. Returns a dict of results for Airtable logging.

    LINKEDIN & X MEDIA RULE (added 2026-09-06 per Tal's explicit instruction,
    supersedes the old video-sharing STANDING RULE): X and LinkedIn NEVER carry
    the HeyGen avatar video. Pass `x_linkedin_image_url` to attach a custom
    static picture (prefer a real Shikkee asset image matched to the day's
    topic) to those two posts instead; leave it None to post text-only on
    X/LinkedIn -- that is a fully acceptable outcome, never a blocker. Only
    Instagram and YouTube carry the video."""
    validate_all(copy)

    heygen = HeyGenClient()
    video_id = heygen.generate_avatar_video(
        script=f"{video_script} {heygen.build_prompt_footer()}",
        avatar_id=ELLA.approved_looks[0],
        voice_id=ELLA.default_voice,
        asset_urls=[real_asset_url],
    )
    video = heygen.wait_for_completion(video_id)
    video_url = video["captioned_video_url"]  # NEVER the plain video_url -- see
    # METRICOOL VIDEO NORMALIZATION note: plain video_url carries an expiring
    # signature and reproducibly fails Metricool's "Failed to normalize media".

    metricool = MetricoolClient()
    today = datetime.now().strftime("%Y-%m-%d")
    results = {}

    results["instagram"] = metricool.create_scheduled_post(
        settings.blog_shikkee_usa,
        f"{today}T{publish_hour_local:02d}:00:00",
        settings.timezone_shikkee_usa,
        {
            "text": copy.instagram,
            "media": [video_url],
            "providers": [{"network": "instagram"}],
            "instagramData": {"type": "REEL", "showReelOnFeed": True, "isAiGenerated": True},
        },
    )
    # LINKEDIN & X MEDIA RULE: never the HeyGen video here -- a custom picture
    # if one was supplied, otherwise no media key at all (text-only is fine).
    x_linkedin_media = {"media": [x_linkedin_image_url]} if x_linkedin_image_url else {}

    results["x"] = metricool.create_scheduled_post(
        settings.blog_shikkee_usa,
        f"{today}T{publish_hour_local:02d}:10:00",
        settings.timezone_shikkee_usa,
        {"text": copy.x, **x_linkedin_media, "providers": [{"network": "twitter"}]},
    )
    results["linkedin"] = metricool.create_scheduled_post(
        settings.blog_shikkee_usa,
        f"{today}T{publish_hour_local:02d}:20:00",
        settings.timezone_shikkee_usa,
        {
            "text": copy.linkedin,
            **x_linkedin_media,
            "providers": [{"network": "linkedin"}],
            "linkedinData": {"type": "post", "previewIncluded": True},
        },
    )
    results["youtube"] = metricool.create_scheduled_post(
        settings.blog_shikkee_usa,
        f"{today}T{publish_hour_local:02d}:30:00",
        settings.timezone_shikkee_usa,
        {
            "text": copy.youtube_description,
            "media": [video_url],
            "providers": [{"network": "youtube"}],
            "youtubeData": {
                "title": copy.youtube_title,
                "type": "short",
                "privacy": "public",
                "madeForKids": False,
                "isAiGeneratedContent": True,
            },
        },
    )
    results["gbp"] = metricool.create_scheduled_post(
        settings.blog_shikkee_usa,
        f"{today}T{publish_hour_local - 1:02d}:00:00",
        settings.timezone_shikkee_usa,
        {
            "text": copy.gbp,
            "media": [real_asset_url],
            "providers": [{"network": "gmb"}],
            "gmbData": {"type": "publication"},
        },
    )

    wp = WordPressClient()
    post = wp.create_draft_post(
        title=copy.blog_title,
        content_html=copy.blog_html,
        slug=copy.blog_slug,
        excerpt=copy.blog_excerpt,
        category_ids=blog_category_ids,
        tag_ids=blog_tag_ids,
    )
    wp.set_featured_media(post["id"], blog_featured_media_id)
    seo_ok, seo_message = wp.push_rankmath_meta(
        post_id=post["id"],
        title=copy.blog_meta_title,
        description=copy.blog_meta_description,
        focus_keyword=copy.blog_focus_keyword,
    )
    results["blog"] = {"post": post, "rankmath_seo_pushed": seo_ok, "rankmath_message": seo_message}

    _log_to_airtable(copy, results, today)
    return results


def _log_to_airtable(copy: ChannelCopy, results: dict, publish_date: str) -> None:
    airtable = AirtableClient()
    # Internal channel keys -> Airtable's actual "platform" singleSelect choice names
    airtable_platform_name = {
        "instagram": "instagram",
        "x": "x",
        "linkedin": "linkedin",
        "gbp": "google",
        "blog": "blog",
        "youtube": "youtube",
    }
    records = []
    for platform in CHANNELS:
        if platform == "blog":
            notes = (
                f"6-CHANNEL DAILY | Blog. WordPress post id {results['blog']['post']['id']}, "
                f"RankMath SEO push {'succeeded' if results['blog']['rankmath_seo_pushed'] else 'BLOCKED: ' + results['blog']['rankmath_message']}"
            )
            caption = copy.blog_excerpt
        else:
            notes = f"6-CHANNEL DAILY | Metricool post id {results[platform]['data']['id']}"
            caption = getattr(copy, "youtube_description" if platform == "youtube" else platform)
        records.append(
            {
                "Publish date": publish_date,
                "platform": airtable_platform_name[platform],
                "Founder account": notes,
                "caption": caption,
                "status": "draft",
                "submmited by": "Claude",
            }
        )
    airtable.create_records(settings.airtable_content_table_id, records)
