package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.BottomSheetScaffold
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SheetValue
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberBottomSheetScaffoldState
import androidx.compose.material3.rememberStandardBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.paging.LoadState
import androidx.paging.PagingData
import androidx.paging.compose.LazyPagingItems
import androidx.paging.compose.collectAsLazyPagingItems
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components.ExploreActiveFiltersRow
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components.ExploreFilterBottomSheet
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components.ExploreSearchBar
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview.ExploreStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.flow.Flow

@OptIn(ExperimentalTime::class, ExperimentalMaterial3Api::class)
@Composable
fun ExploreScreen(
    modifier: Modifier = Modifier,
    posts: LazyPagingItems<ExploreArticle>,
    state: ExploreState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onExploreEvent: (ExploreEvent) -> Unit,
) {

    val bottomSheetState = rememberStandardBottomSheetState(
        initialValue = SheetValue.Hidden,
        skipHiddenState = false,
    )
    val scaffoldState = rememberBottomSheetScaffoldState(
        bottomSheetState = bottomSheetState
    )

    LaunchedEffect(key1 = state.isFilterSheetOpen) {
        if (state.isFilterSheetOpen) bottomSheetState.expand() else bottomSheetState.hide()
    }

    BackHandler(enabled = state.isFilterSheetOpen) {
        onExploreEvent(ExploreEvent.DismissFilterSheet)
    }

    val refreshState = posts.loadState.refresh
    val hasCurrentArticles = posts.itemSnapshotList.items.firstOrNull()?.filter == state.filter
    val currentOptions = if (state.hasCurrentFilterOptions) state.filterOptions else ExploreFilterOptions()

    BottomSheetScaffold(
        modifier = Modifier.then(modifier),
        scaffoldState = scaffoldState,
        sheetPeekHeight = 0.dp,
        sheetDragHandle = null,
        sheetSwipeEnabled = false,
        sheetShape = RoundedCornerShape(
            topStart = 16.dp,
            topEnd = 16.dp,
        ),
        sheetContainerColor = MaterialTheme.colorScheme.surface,
        sheetContentColor = MaterialTheme.colorScheme.onSurface,
        sheetContent = {
            ExploreFilterBottomSheet(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(
                        width = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface,
                        shape = RoundedCornerShape(
                            topStart = 16.dp,
                            topEnd = 16.dp,
                        ),
                    ),
                draftFilter = state.draftFilter,
                filterOptions = currentOptions,
                isLoadingOptions = !state.hasCurrentFilterOptions && refreshState !is LoadState.Error,
                optionsFailed = !state.hasCurrentFilterOptions && refreshState is LoadState.Error,
                onRetryOptions = posts::retry,
                onDraftFilterChange = { onExploreEvent(ExploreEvent.UpdateDraftFilter(filter = it)) },
                onApply = {
                    onExploreEvent(ExploreEvent.ApplyDraftFilter)
                },
                onReset = { onExploreEvent(ExploreEvent.ResetDraftFilters) },
                onDismiss = {
                    onExploreEvent(ExploreEvent.DismissFilterSheet)
                },
            )
        },
    ) { _ ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            ExploreSearchBar(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp),
                query = state.query,
                hasActiveFilters = state.hasActiveFilters,
                activeFilterCount = state.activeFilterCount,
                onQueryChange = { onExploreEvent(ExploreEvent.UpdateQuery(query = it)) },
                onSearch = { onExploreEvent(ExploreEvent.SubmitQuery) },
                onOpenFilter = {
                    onExploreEvent(ExploreEvent.OpenFilterSheet)
                },
            )

            if (state.hasActiveFilters) {
                ExploreActiveFiltersRow(
                    modifier = Modifier.fillMaxWidth(),
                    filter = state.filter,
                    filterOptions = state.filterOptions,
                    onRemoveCategory = { onExploreEvent(ExploreEvent.RemoveCategory(category = it)) },
                    onRemoveLanguage = { onExploreEvent(ExploreEvent.RemoveLanguage(language = it)) },
                    onRemoveSource = { onExploreEvent(ExploreEvent.RemoveSource(sourceId = it)) },
                    onClearDateRange = { onExploreEvent(ExploreEvent.ClearDateRange) },
                    onResetSort = { onExploreEvent(ExploreEvent.ChangeSort(sort = "freshness")) },
                    onClearAll = { onExploreEvent(ExploreEvent.ClearAllFilters) },
                )
            }

            when {
                !hasCurrentArticles && refreshState !is LoadState.Error &&
                    (refreshState is LoadState.Loading || !state.hasCurrentFilterOptions) -> {
                    ShimmerGroup {
                        LazyColumn(
                            modifier = Modifier
                                .fillMaxSize()
                                .weight(1f),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                        ) {
                            items(count = 5) {
                                Column(
                                    modifier = Modifier.padding(vertical = 12.dp),
                                    verticalArrangement = Arrangement.spacedBy(12.dp),
                                ) {
                                    ShimmerItem(
                                        modifier = Modifier
                                            .fillMaxWidth(fraction = 0.3f)
                                            .height(16.dp),
                                        isLoading = true,
                                    ) {}
                                    repeat(times = 2) {
                                        ShimmerItem(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .height(24.dp),
                                            isLoading = true,
                                        ) {}
                                    }
                                }
                            }
                        }
                    }
                }

                refreshState is LoadState.Error && !hasCurrentArticles -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .weight(1f)
                            .padding(16.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Text(
                                text = stringResource(R.string.explore_load_error),
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.error,
                                textAlign = TextAlign.Center,
                            )
                            OutlinedButton(onClick = posts::retry) {
                                Text(text = stringResource(R.string.home_retry))
                            }
                        }
                    }
                }

                !hasCurrentArticles -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .weight(1f)
                            .padding(16.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            text = stringResource(R.string.explore_empty),
                            style = MaterialTheme.typography.bodyLarge,
                            textAlign = TextAlign.Center,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        )
                    }
                }

                else -> {
                    LazyColumn(
                        modifier = Modifier
                            .weight(1f)
                            .padding(top = 6.dp),
                        verticalArrangement = Arrangement.spacedBy(0.dp),
                    ) {
                        when (refreshState) {
                            is LoadState.Loading -> item(key = "refresh_loading") {
                                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                            }
                            is LoadState.Error -> item(key = "refresh_error") {
                                Column(
                                    modifier = Modifier.padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp),
                                ) {
                                    Text(
                                        text = stringResource(R.string.explore_load_error),
                                        color = MaterialTheme.colorScheme.error,
                                    )
                                    OutlinedButton(onClick = posts::retry) {
                                        Text(text = stringResource(R.string.home_retry))
                                    }
                                }
                            }
                            else -> Unit
                        }
                        items(
                            count = posts.itemCount,
                            key = { index -> posts.peek(index)?.post?.id ?: "explore_$index" },
                        ) { index ->
                            val article = posts[index] ?: return@items
                            if (article.filter != state.filter) return@items
                            val post = article.post
                            PostRow(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp),
                                title = post.title,
                                source = post.sourceTitle,
                                onClick = {
                                    onNavigationEvent(
                                        if (post.hasContent) {
                                            MainNavigationEvent.ShowPostDetails(postId = post.id)
                                        } else {
                                            MainNavigationEvent.OpenCustomTab(url = post.url)
                                        }
                                    )
                                },
                            )
                            HorizontalDivider(
                                modifier = Modifier.fillMaxWidth(),
                                thickness = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f),
                            )
                        }
                        when (posts.loadState.append) {
                            is LoadState.Loading -> item(key = "append_loading") {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(16.dp),
                                    contentAlignment = Alignment.Center,
                                ) {
                                    CircularProgressIndicator()
                                }
                            }
                            is LoadState.Error -> item(key = "append_error") {
                                Column(
                                    modifier = Modifier.padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp),
                                ) {
                                    Text(
                                        text = stringResource(R.string.explore_append_error),
                                        color = MaterialTheme.colorScheme.error,
                                    )
                                    OutlinedButton(onClick = posts::retry) {
                                        Text(text = stringResource(R.string.home_retry))
                                    }
                                }
                            }
                            else -> Unit
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalTime::class, ExperimentalMaterial3Api::class)
@PreviewLightDark
@Composable
fun ExploreScreenPreview(
    @PreviewParameter(ExploreStateProvider::class) previewContent: Pair<ExploreState, Flow<PagingData<ExploreArticle>>>,
) {

    val (exploreState, content) = previewContent

    BrieflyTheme {
        Surface {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = {
                    TopAppBar(
                        onMenuSelect = {},
                    )
                },
            ) { paddingValues ->
                ExploreScreen(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    state = exploreState,
                    posts = content.collectAsLazyPagingItems(),
                    onNavigationEvent = {},
                    onExploreEvent = {},
                )
            }
        }
    }
}
