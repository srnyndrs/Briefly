package com.srnyndrs.android.briefly.ui.screen.main.navigation

sealed class MainNavigationEvent {
    data class ShowPostDetails(val postId: String): MainNavigationEvent()
    data class ShowSourceDetails(val sourceId: String): MainNavigationEvent()
    data class OpenCustomTab(val url: String?): MainNavigationEvent()
    data object NavigateBack: MainNavigationEvent()
}
