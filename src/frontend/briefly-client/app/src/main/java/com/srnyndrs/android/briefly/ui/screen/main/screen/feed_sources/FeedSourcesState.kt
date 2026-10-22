package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.ui.model.UiState

data class FeedSourcesState(
    val searchText: String = "",
    val results: UiState<List<Source>> = UiState.Idle,
    val isRefreshing: Boolean = false,
    val refreshError: String? = null,
)
