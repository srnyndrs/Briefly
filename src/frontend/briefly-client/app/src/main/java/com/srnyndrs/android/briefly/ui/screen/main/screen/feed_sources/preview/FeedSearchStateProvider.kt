package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesState

class FeedSourcesStateProvider: PreviewParameterProvider<FeedSourcesState> {
    override val values: Sequence<FeedSourcesState>
        get() = sequenceOf(
            FeedSourcesState(
                results = UiState.Loading
            ),
            FeedSourcesState(
                results = UiState.Success(
                    data = listOf(
                        Source(
                            id = "1",
                            title = "Telex.hu",
                            url = "https://telex.hu/rss",
                            favicon = null
                        ),
                        Source(
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
