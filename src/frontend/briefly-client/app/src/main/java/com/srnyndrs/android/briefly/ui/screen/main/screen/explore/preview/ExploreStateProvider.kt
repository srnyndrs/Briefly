package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.FilterSource
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
class ExploreStateProvider : PreviewParameterProvider<Pair<ExploreState, Flow<PagingData<Post>>>> {
    override val values = sequenceOf(
        ExploreState(
            query = "",
            filter = ExplorePostFilter(
                categories = listOf("Technology"),
                languages = listOf("en"),
                sort = "freshness",
            ),
            filterOptions = ExploreFilterOptions(
                categories = listOf("Politics", "Technology", "Science", "Business", "Culture"),
                languages = listOf("en", "hu", "de"),
                sources = listOf(
                    FilterSource("1", "The Verge"),
                    FilterSource("2", "Ars Technica"),
                    FilterSource("3", "Reuters"),
                ),
            ),
        ) to flowOf(
            PagingData.from(
                data = listOf(
                    Post(
                        id = "1",
                        title = "Itthon és Európában is duplázna a kínai óriás, amely Magyarországon már előzi a Teslát",
                        description = "This is really important",
                        imageUrl = "",
                        category = "Külföld",
                        source = "24.hu",
                    ),
                    Post(
                        id = "2",
                        title = "Bérfizetési probléma: egy hévízi háromcsillagos szálloda dolgozói nem kapták meg fizetésüket",
                        description = "This is really important",
                        imageUrl = "",
                        category = "Belföld",
                        source = "Telex",
                    ),
                    Post(
                        id = "3",
                        title = "Elárulta az ETO edzője, hol folytatja a pályafutását",
                        description = "This is really important",
                        imageUrl = "",
                        category = "Sport",
                        source = "24.hu",
                    ),
                )
            )
        )
    )
}
