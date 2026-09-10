package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.SourceDetailsState
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

class SourceDetailsStateProvider : PreviewParameterProvider<SourceDetailsState> {
    @OptIn(ExperimentalTime::class)
    override val values = sequenceOf(
        SourceDetailsState(
            feedDetails = UiState.Loading,
            articles = UiState.Loading,
        ),
        SourceDetailsState(
            feedDetails = UiState.Success(
                data = SourceDetails(
                    id = "1",
                    websiteUrl = "",
                    title = "24.hu",
                    description = "Hírek, podcastek és egyebek! Mindent megtalálsz, amit szeretnél a nap 24 órájában!",
                    imageUrl = "",
                    followed = true,
                    subscribed = false,
                    lastUpdatedAt = Instant.parse("2026-05-22T12:36:11Z"),
                ),
            ),
            articles = UiState.Success(
                data = listOf(
                    Post(
                        id = "1",
                        title = "Itthon és Európában is duplázna a kínai óriás, amely Magyarországon már elérhetővé tette a Teslát",
                        description = "This is really important",
                        imageUrl = "asd",
                        category = "Külföld",
                        source = "24.hu",
                        publishDate = Instant.parse("2026-05-22T12:36:11Z"),
                    ),
                    Post(
                        id = "3",
                        title = "Elárulta az ETO edzője, hol folytatja a pályafutását",
                        description = "This is really important",
                        imageUrl = "asd",
                        category = "Foci",
                        source = "24.hu",
                        publishDate = Instant.parse("2026-05-21T12:36:11Z"),
                    ),
                    Post(
                        id = "4",
                        title = "\"Biztos, hogy nem\" – Havasi Bertalan karrierjének emlékére",
                        description = "This is really important",
                        imageUrl = "asd",
                        category = "Belföld",
                        source = "24.hu",
                        publishDate = Instant.parse("2026-05-20T12:36:11Z"),
                    ),
                ),
            ),
        ),
    )
}
