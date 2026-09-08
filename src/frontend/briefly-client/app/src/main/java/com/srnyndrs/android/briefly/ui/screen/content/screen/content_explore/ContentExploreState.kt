package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore

import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.ui.model.UiState

data class ContentExploreState(
    val result: UiState<PostPagingResult> = UiState.Idle,
)
