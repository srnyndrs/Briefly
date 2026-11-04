package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

sealed interface FeedSourcesEvent {
    data class SelectDiscoverySource(val url: String) : FeedSourcesEvent
    data class UpdateDiscoverySource(val source: com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult) : FeedSourcesEvent
    data object DismissDiscoverySource : FeedSourcesEvent
    data class UpdateDiscoveryUrl(val url: String): FeedSourcesEvent
    data object Discover: FeedSourcesEvent
    data object RetryDiscovery: FeedSourcesEvent
    data class AddSource(val url: String): FeedSourcesEvent
    data class UpdateSearchText(val text: String): FeedSourcesEvent
    data object SearchFeedSource: FeedSourcesEvent
    data object RetrySearch: FeedSourcesEvent
}
