package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDetails
import com.srnyndrs.android.briefly.ui.model.UiState

data class SourceDetailsState(
    val blockStatus: UiState<Boolean> = UiState.Idle,
    val isUpdatingBlock: Boolean = false,
    val blockUpdateFailed: Boolean = false,
    val isUpdatingSubscription: Boolean = false,
    val subscriptionUpdateFailed: Boolean = false,
    val feedDetails: UiState<SourceDetails> = UiState.Idle,
    val articles: UiState<List<Post>> = UiState.Idle,
)
