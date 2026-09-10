package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

sealed class SourceDetailsEvent {
    data class ToggleFollow(val followed: Boolean): SourceDetailsEvent()
    data class ToggleSubscribe(val subscribed: Boolean): SourceDetailsEvent()
}
