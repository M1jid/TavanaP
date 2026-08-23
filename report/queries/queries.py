from enum import Enum


class QueryTypes(str, Enum):
# ====================================================================================================
    
    # Telegram Queries
    TelegramTopTrendsTitle = "queries/telegram/telegram_top_trends_title.j2"
    TelegramTopTrendsOverview = "queries/telegram/telegram_top_trends_overview.j2"
    TelegramSourceTracing = "queries/telegram/telegram_sourcetracing.j2"
    TelegramOwnedChannelsReport = "queries/telegram/telegram_owned_channels_report.j2"
    TelegramChannelInsights = "queries/telegram/telegram_channel_insights.j2"
    TelegramSimilarChannels = "queries/telegram/telegram_similar_channels.j2"
    TelegramGetChannel = "queries/telegram/telegram_get_channel.j2"
    TelegramKeywordTopChannels = "queries/telegram/telegram_keyword_top_channels.j2"
    TelegramGeographicReport = "queries/telegram/telegram_geographic_report.j2"
    TelegramContentReportTags = "queries/telegram/telegram_content_report_tags.j2"
    TelegramContentReportNoTags = "queries/telegram/telegram_content_report_no_tags.j2"
    TelegramRelationsByForwarding = "queries/telegram/telegram_relations_by_forwarding.j2"
    TelegramChannelDetailsByPeerID = "queries/telegram/telegram_channel_details_by_peer_id.j2"
    TelegramChannelInfoByURL = "queries/telegram/telegram_channel_info_by_url.j2"
    TelegramAjaChannelsMessages = "queries/telegram/telegram_aja_channels_messages.j2"
    TelegramQueryByMessages = "queries/telegram/telegram_query_by_messages.j2"
    TelegramQueryByAggs = "queries/telegram/telegram_query_by_aggs.j2"
    TelegramChatScroll = "queries/telegram/telegram_chat_scroll.j2"
    TelegramChatPeersScroll = "queries/telegram/telegram_chat_peers_scroll.j2"
    TelegramAjaSubsGrowth = "queries/telegram/telegram_aja_subs_growth.j2"

    # Telegram Daily Report Queries
    TelegramDailyPopularPost = 'queries/telegram/telegram_daily_popular_posts.j2'
    TelegramDailyPopularChannel = 'queries/telegram/telegram_daily_popular_channels.j2'
    TelegramDailySimilarMessage = 'queries/telegram/telegram_daily_similar_messages.j2'
    TelegramDailyTrendingNewsSummary = 'queries/telegram/telegram_daily_trending_news_summary.j2'
    TelegramDailyMostReactionChannel = 'queries/telegram/telegram_daily_most_reaction_channels.j2'
    TelegramDailyMostCommentChannel = 'queries/telegram/telegram_daily_most_comment_channels.j2'

    # WordCloud Queries
    TelegramUserWordCloud = "queries/telegram/telegram_user_wordcloud.j2"
    TelegramWordCloud = "queries/telegram/telegram_wordcloud.j2"
    TelegramOwnedChannelsWordCloud = "queries/telegram/telegram_owned_channels_wordcloud.j2"
    TelegramChannelWordCloud = "queries/telegram/telegram_channel_wordcloud.j2"
    TelegramGroupWordCloud = "queries/telegram/telegram_group_wordcloud.j2"

    # User Queries
    TelegramUserJoinedChannels = "queries/telegram/telegram_user_joined_channels.j2"

    # Posts Queries
    TelegramUpdatePosts = "queries/telegram/telegram_update_posts.j2"

# ====================================================================================================
    
    # Instagram Queries
    InstagramTopTrend = "queries/instagram/instagram_top_trend.j2"
    InstagramPagePostsByUsername = "queries/instagram/channel_info_by_url.j2"
    InstagramFilters = "queries/instagram/instagram_filters.j2" # Query by Topic, Person, Event and Force
    InstagramSourcetracing = "queries/instagram/instagram_sourcetracing.j2"

# ====================================================================================================

    # RSS Queries
    RSSQueryByMessages = "queries/rss/rss_query_by_messages.j2"
    RSSQueryByAggs = "queries/rss/rss_query_by_aggs.j2"
    RSSInfoByURL = "queries/rss/rss_info_by_url.j2"

# ====================================================================================================

    # Default Queries
    DefaultDailyReceivedMessages = "queries/default/default_daily_received_messages.j2"

# ====================================================================================================