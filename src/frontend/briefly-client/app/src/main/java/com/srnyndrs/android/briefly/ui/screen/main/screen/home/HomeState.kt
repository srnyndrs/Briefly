package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.ui.model.UiState

data class HomeState(
    val result: UiState<PostPagingResult> = UiState.Idle,
)
