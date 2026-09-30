package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

sealed interface FeedSourcesEvent {
    data class UpdateSearchText(val text: String) : FeedSourcesEvent
    data object SearchFeedSource : FeedSourcesEvent
    data object RetrySearch : FeedSourcesEvent
}
