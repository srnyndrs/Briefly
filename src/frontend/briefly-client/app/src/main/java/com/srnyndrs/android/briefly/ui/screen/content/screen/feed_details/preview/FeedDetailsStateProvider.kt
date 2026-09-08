package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details.FeedDetailsState
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

class FeedDetailsStateProvider: PreviewParameterProvider<FeedDetailsState> {
    @OptIn(ExperimentalTime::class)
    override val values = sequenceOf(
        FeedDetailsState(
            feedDetails = UiState.Loading,
            articles = UiState.Loading
        ),
        FeedDetailsState(
            feedDetails = UiState.Success(
                data = SourceDetails(
                    id = "1",
                    websiteUrl = "",
                    title = "24.hu",
                    description = "Hírek, podcastek és egyebek! Minden megtalálsz amit szeretnél a nap 24 órájában!",
                    imageUrl = "",
                    followed = true,
                    subscribed = false,
                    lastUpdatedAt = Instant.parse("2026-05-22T12:36:11Z")
                )
            ),
            articles = UiState.Success(
                data = listOf(
                    Post(
                        id = "1",
                        title = "Itthon és Európában is duplázna a kínai óriás, amely Magyarországon már előzi a Teslát",
                        description = "This is really important",
                        imageUrl = "asd",
                        category = "Külföld",
                        source = "24.hu"
                    ),
                    Post(
                        id = "3",
                        title = "Elárulta az ETO edzője, hol folytatja a pályafutását",
                        description = "This is really important",
                        imageUrl = "asd",
                        category = "Foci",
                        source = "24.hu"
                    ),
                    Post(
                        id = "4",
                        title = "\"Biztos, hogy nem\" – Havasi Bertalan karrierjének emlékére",
                        description = "This is really important",
                        imageUrl = "asd",
                        category = "Belföld",
                        source = "24.hu"
                    ),
                )
            )
        )
    )
}
