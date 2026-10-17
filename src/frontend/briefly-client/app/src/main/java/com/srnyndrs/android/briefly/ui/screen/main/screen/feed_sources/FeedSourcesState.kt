package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.ui.model.UiState

data class FeedSourcesState(
    val results: UiState<List<Source>> = UiState.Idle
)
