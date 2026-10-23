package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import androidx.paging.LoadState
import androidx.paging.LoadStates
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.FilterSource
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreArticle
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreState
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf

@OptIn(ExperimentalTime::class)
object ExplorePreviewData {
    val state = ExploreState(
        filterOptions = ExploreFilterOptions(
            categories = listOf("science", "technology"),
            languages = listOf("en", "hu"),
            sources = listOf(
                FilterSource(
                    id = "science-daily",
                    title = "Daily Science",
                ),
            ),
        ),
        filterOptionsFilter = ExplorePostFilter(sort = "freshness"),
    )
    val article = ExploreArticle(
        post = Post(
            id = "battery-research",
            title = "Researchers improve recovery of materials from used batteries",
            sourceTitle = "Daily Science",
        ),
        filter = state.filter,
    )
}

@OptIn(ExperimentalTime::class)
class ExploreStateProvider: PreviewParameterProvider<Pair<ExploreState, Flow<PagingData<ExploreArticle>>>> {
    override val values = sequenceOf(
        ExplorePreviewData.state to pages(articles = listOf(ExplorePreviewData.article)),
        ExplorePreviewData.state to pages(),
        ExploreState() to pages(refresh = LoadState.Loading),
        ExploreState() to pages(refresh = LoadState.Error(error = IllegalStateException())),
        ExplorePreviewData.state to pages(
            articles = listOf(ExplorePreviewData.article),
            refresh = LoadState.Loading,
        ),
        ExplorePreviewData.state to pages(
            articles = listOf(ExplorePreviewData.article),
            refresh = LoadState.Error(error = IllegalStateException()),
        ),
    )

    private fun pages(
        articles: List<ExploreArticle> = emptyList(),
        refresh: LoadState = LoadState.NotLoading(endOfPaginationReached = true),
    ): Flow<PagingData<ExploreArticle>> = flowOf(
        PagingData.from(
            data = articles,
            sourceLoadStates = LoadStates(
                refresh = refresh,
                prepend = LoadState.NotLoading(endOfPaginationReached = true),
                append = LoadState.NotLoading(endOfPaginationReached = true),
            ),
        ),
    )
}
