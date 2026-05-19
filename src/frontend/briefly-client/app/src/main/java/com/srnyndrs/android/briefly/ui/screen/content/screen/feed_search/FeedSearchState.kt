package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search

import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.ui.model.UiState

data class FeedSearchState(
    val results: UiState<List<FeedSourceResultItem>> = UiState.Idle
)
