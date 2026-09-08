package com.srnyndrs.android.briefly.ui.screen.content.screen.article_details

import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.ui.model.UiState

data class ArticleDetailsState(
    val details: UiState<PostDetails>
)
