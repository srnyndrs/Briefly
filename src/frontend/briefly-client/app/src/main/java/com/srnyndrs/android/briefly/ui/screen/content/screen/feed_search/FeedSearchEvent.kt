package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search

sealed class FeedSearchEvent {
    data class SearchFeedSource(val query: String? = null): FeedSearchEvent()
    data class SubscribeFeedSource(val sourceId: String): FeedSearchEvent()
    data class UnsubscribeFeedSource(val sourceId: String): FeedSearchEvent()
}
