package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.ui.model.UiState

data class FeedDetailsState(
    val feedDetails: UiState<SourceDetails> = UiState.Idle,
    val articles: UiState<List<Post>> = UiState.Idle,
)
