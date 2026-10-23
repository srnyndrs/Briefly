package com.srnyndrs.android.briefly.ui.screen.main.screen.home.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.HomeArticle
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.HomeState
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf

@OptIn(ExperimentalTime::class)
class HomeStateProvider : PreviewParameterProvider<Pair<HomeState, Flow<PagingData<HomeArticle>>>> {
    private val headlines = listOf(
        Post(
            id = "1",
            title = "New electric bus routes connect Budapest's outer districts",
            description = "The city will introduce more frequent services from next month.",
            sourceTitle = "Telex",
            categories = listOf(Category.SOCIETY),
        ),
        Post(
            id = "2",
            title = "European researchers publish new battery recycling results",
            description = "The process recovers more material from used electric vehicle batteries.",
            sourceTitle = "24.hu",
            categories = listOf(Category.SCIENCE),
        ),
    )

    override val values = sequenceOf(
        HomeState(
            headlines = headlines,
            categories = Category.entries,
        ) to flowOf(
            PagingData.from(
                data = listOf(
                    HomeArticle(
                        post = Post(
                            id = "3",
                            title = "Local libraries extend their weekend opening hours",
                            sourceTitle = "Telex",
                            categories = listOf(Category.SOCIETY),
                        ),
                        category = null,
                    ),
                ),
            ),
        ),
    )
}
