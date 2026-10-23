package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesState

class FeedSourcesStateProvider : PreviewParameterProvider<FeedSourcesState> {
    private val sources = listOf(
        Source(
            id = "1",
            title = "Telex.hu",
            url = "https://telex.hu/rss",
            verified = true,
        ),
        Source(
            id = "2",
            title = "24.hu",
            url = "https://24.hu/feed",
            verified = true,
        ),
        Source(
            id = "3",
            title = "Example News with a longer source title",
            url = "https://example.com/feed",
        ),
    )

    override val values = sequenceOf(
        FeedSourcesState(results = UiState.Loading),
        FeedSourcesState(results = UiState.Success(data = sources)),
        FeedSourcesState(
            searchText = "Science",
            results = UiState.Success(data = emptyList()),
        ),
        FeedSourcesState(results = UiState.Error(message = "Preview failure")),
        FeedSourcesState(
            results = UiState.Success(data = sources),
            isRefreshing = true,
        ),
        FeedSourcesState(
            results = UiState.Success(data = sources),
            refreshError = "Preview failure",
        ),
    )
}
