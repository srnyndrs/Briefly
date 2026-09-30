package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

sealed class FeedSourcesEvent {
    data class SearchFeedSource(val query: String? = null): FeedSourcesEvent()
    data class SubscribeFeedSource(val sourceId: String): FeedSourcesEvent()
    data class UnsubscribeFeedSource(val sourceId: String): FeedSourcesEvent()
}
