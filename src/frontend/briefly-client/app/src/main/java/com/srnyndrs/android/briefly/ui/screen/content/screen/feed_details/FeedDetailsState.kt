package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.ui.model.UiState

data class FeedDetailsState(
    val feedDetails: UiState<FeedSourceDetails> = UiState.Idle,
    val articles: UiState<List<ArticleItem>> = UiState.Idle,
)
