package com.srnyndrs.android.briefly.ui.screen.content.navigation

sealed class ContentNavigationEvent {
    data class ShowArticleDetails(val articleId: String): ContentNavigationEvent()
    data class ShowFeedDetails(val sourceId: String): ContentNavigationEvent()
    data class OpenCustomTab(val url: String?): ContentNavigationEvent()
    data object NavigateBack: ContentNavigationEvent()
}
