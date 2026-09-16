package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
class ExploreStateProvider: PreviewParameterProvider<Pair<ExploreState, Flow<PagingData<Post>>>> {
    override val values = sequenceOf(
        ExploreState() to flowOf(PagingData.from(
            data = listOf(
                Post(
                    id = "1",
                    title = "Itthon és Európában is duplázna a kínai óriás, amely Magyarországon már előzi a Teslát",
                    description = "This is really important",
                    imageUrl = "",
                    category = "Külföld",
                    source = "24.hu"
                ),
                Post(
                    id = "2",
                    title = "Bérfizetési probléma: egy hévízi háromcsillagos szálloda dolgozói nem kapták meg fizetésüket",
                    description = "This is really important",
                    imageUrl = "",
                    category = "Belföld",
                    source = "Telex"
                ),
                Post(
                    id = "3",
                    title = "Elárulta az ETO edzője, hol folytatja a pályafutását",
                    description = "This is really important",
                    imageUrl = "",
                    category = "Sport",
                    source = "24.hu"
                )
            )
        ))
    )
}
