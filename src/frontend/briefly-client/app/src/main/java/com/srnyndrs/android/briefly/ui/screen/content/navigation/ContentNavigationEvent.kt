package com.srnyndrs.android.briefly.ui.screen.content.navigation

sealed class ContentNavigationEvent {
    data class ShowPostDetails(val postId: String): ContentNavigationEvent()
    data class ShowSourceDetails(val sourceId: String): ContentNavigationEvent()
    data class OpenCustomTab(val url: String?): ContentNavigationEvent()
    data object NavigateBack: ContentNavigationEvent()
}
