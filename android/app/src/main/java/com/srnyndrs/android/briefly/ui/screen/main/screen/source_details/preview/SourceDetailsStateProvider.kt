package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDetails
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.SourceDetailsState
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
class SourceDetailsStateProvider : PreviewParameterProvider<SourceDetailsState> {
    private val ready = SourceDetailsState(
        blockStatus = UiState.Success(data = false),
        feedDetails = UiState.Success(
            data = SourceDetails(
                id = "source",
                siteUrl = "https://24.hu",
                title = "24.hu",
                description = "News, interviews, and reporting from Hungary and around the world.",
                isSubscribed = false,
                verified = true,
                lastUpdatedAt = Instant.parse(input = "2026-10-19T12:00:00Z"),
            ),
        ),
        articles = UiState.Success(
            data = listOf(
                Post(
                    id = "article",
                    title = "Local libraries extend their weekend opening hours",
                    description = "The new schedule gives readers more time to visit.",
                    sourceTitle = "24.hu",
                    publishedAt = Instant.parse(input = "2026-10-19T11:00:00Z"),
                ),
            ),
        ),
    )

    override val values = sequenceOf(
        SourceDetailsState(
            blockStatus = UiState.Loading,
            feedDetails = UiState.Loading,
            articles = UiState.Loading,
        ),
        ready,
        ready.copy(feedDetails = UiState.Error(message = "Preview failure")),
        ready.copy(articles = UiState.Error(message = "Preview failure")),
        ready.copy(isUpdatingSubscription = true),
        ready.copy(subscriptionUpdateFailed = true),
        ready.copy(isUpdatingBlock = true),
        ready.copy(blockUpdateFailed = true),
        ready.copy(blockStatus = UiState.Error(message = "Preview failure")),
    )
}
