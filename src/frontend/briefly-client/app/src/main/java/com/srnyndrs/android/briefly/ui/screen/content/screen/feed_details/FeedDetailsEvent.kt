package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

sealed class FeedDetailsEvent {
    data object FollowFeed: FeedDetailsEvent()
    data object UnfollowFeed: FeedDetailsEvent()
}
