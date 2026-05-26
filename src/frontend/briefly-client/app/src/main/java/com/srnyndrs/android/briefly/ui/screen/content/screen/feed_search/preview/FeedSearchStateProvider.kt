package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search.FeedSearchState

class FeedSearchStateProvider: PreviewParameterProvider<FeedSearchState> {
    override val values: Sequence<FeedSearchState>
        get() = sequenceOf(
            FeedSearchState(
                results = UiState.Loading
            ),
            FeedSearchState(
                results = UiState.Success(
                    data = listOf(
                        FeedSourceResultItem(
                            id = "1",
                            title = "Telex.hu",
                            url = "https://telex.hu/rss",
                            favicon = null
                        ),
                        FeedSourceResultItem(
                            id = "2",
                            title = "24.hu",
                            url = "https://24.hu/feed",
                            favicon = null
                        )
                    )
                )
            )
        )
}