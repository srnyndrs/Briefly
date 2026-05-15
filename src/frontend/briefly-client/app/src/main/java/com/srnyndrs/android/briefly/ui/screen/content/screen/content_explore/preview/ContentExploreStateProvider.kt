package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.ContentExploreState

class ContentExploreStateProvider: PreviewParameterProvider<ContentExploreState> {
    override val values = sequenceOf(
        ContentExploreState(
            page = 1,
            count = 1,
            result = UiState.Success(
                ArticlePagingResult(
                    page = 1,
                    count = 5,
                    items = listOf(
                        ArticleItem(
                            id = "1",
                            title = "Breaking news!",
                            description = "This is really important",
                            imageUrl = "asd",
                        )
                    )
                )
            )
        )
    )
}