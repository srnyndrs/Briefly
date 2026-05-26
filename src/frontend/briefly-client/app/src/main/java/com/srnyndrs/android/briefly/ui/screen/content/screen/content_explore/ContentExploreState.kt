package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore

import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.ui.model.UiState

data class ContentExploreState(
    val result: UiState<ArticlePagingResult> = UiState.Idle,
)
