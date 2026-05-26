package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

sealed class FeedDetailsEvent {
    data class ToggleFollow(val followed: Boolean): FeedDetailsEvent()
    data class ToggleSubscribe(val subscribed: Boolean): FeedDetailsEvent()
}
