package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

sealed class SourceDetailsEvent {
    data object RetryBlockStatus : SourceDetailsEvent()
    data object ToggleBlock : SourceDetailsEvent()
    data object RetryFeedDetails : SourceDetailsEvent()
    data object RetryArticles : SourceDetailsEvent()
    data object ToggleSubscribe : SourceDetailsEvent()
}
