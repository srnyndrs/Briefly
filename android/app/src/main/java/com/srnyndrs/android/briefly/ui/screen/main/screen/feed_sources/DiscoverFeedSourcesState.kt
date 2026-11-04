package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.ui.model.UiState

data class DiscoverFeedSourcesState(
    val selectedSource: SourceDiscoveryResult? = null,
    val url: String = "",
    val results: UiState<List<SourceDiscoveryResult>> = UiState.Idle,
    val isRefreshing: Boolean = false,
    val refreshFailed: Boolean = false,
    val additions: Map<String, UiState<String>> = emptyMap(),
    val duplicateUrls: Set<String> = emptySet(),
)
