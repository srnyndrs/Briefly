package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.BottomSheetScaffold
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.runtime.rememberCoroutineScope
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
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components.ExploreActiveFiltersRow
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components.ExploreFilterBottomSheet
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components.ExploreSearchBar
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview.ExploreStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class, ExperimentalMaterial3Api::class)
@Composable
fun ExploreScreen(
    modifier: Modifier = Modifier,
    posts: LazyPagingItems<Post>,
    state: ExploreState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onExploreEvent: (ExploreEvent) -> Unit,
) {

    val scope = rememberCoroutineScope()
    val bottomSheetState = rememberStandardBottomSheetState(
        initialValue = SheetValue.Hidden,
        skipHiddenState = false,
        confirmValueChange = { targetValue ->
            targetValue != SheetValue.PartiallyExpanded
        },
    )
    val scaffoldState = rememberBottomSheetScaffoldState(
        bottomSheetState = bottomSheetState,
    )

    LaunchedEffect(state.isFilterSheetOpen) {
        if (state.isFilterSheetOpen) {
            bottomSheetState.expand()
        } else if (bottomSheetState.isVisible) {
            bottomSheetState.hide()
        }
    }

    LaunchedEffect(bottomSheetState.currentValue) {
        if (bottomSheetState.currentValue == SheetValue.Hidden && state.isFilterSheetOpen) {
            onExploreEvent(ExploreEvent.DismissFilterSheet)
        }
    }

    BackHandler(enabled = bottomSheetState.isVisible) {
        scope.launch { bottomSheetState.hide() }
        onExploreEvent(ExploreEvent.DismissFilterSheet)
    }

    val refreshState = posts.loadState.refresh

    BottomSheetScaffold(
        modifier = modifier.fillMaxSize(),
        scaffoldState = scaffoldState,
        sheetPeekHeight = 0.dp,
        sheetDragHandle = null,
        sheetSwipeEnabled = bottomSheetState.isVisible || state.isFilterSheetOpen,
        sheetShape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        sheetContainerColor = MaterialTheme.colorScheme.surface,
        sheetContentColor = MaterialTheme.colorScheme.onSurface,
        sheetContent = {
            ExploreFilterBottomSheet(
                modifier = Modifier.fillMaxWidth(),
                draftFilter = state.draftFilter,
                filterOptions = state.filterOptions,
                onDraftFilterChange = { onExploreEvent(ExploreEvent.UpdateDraftFilter(it)) },
                onApply = {
                    scope.launch { bottomSheetState.hide() }
                    onExploreEvent(ExploreEvent.ApplyDraftFilter)
                },
                onReset = { onExploreEvent(ExploreEvent.ResetDraftFilters) },
                onDismiss = {
                    scope.launch { bottomSheetState.hide() }
                    onExploreEvent(ExploreEvent.DismissFilterSheet)
                },
            )
        },
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            ExploreSearchBar(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                query = state.query,
                hasActiveFilters = state.hasActiveFilters,
                activeFilterCount = state.activeFilterCount,
                onQueryChange = { onExploreEvent(ExploreEvent.UpdateQuery(it)) },
                onSearch = { onExploreEvent(ExploreEvent.SubmitQuery) },
                onOpenFilter = {
                    onExploreEvent(ExploreEvent.OpenFilterSheet)
                    scope.launch { bottomSheetState.expand() }
                },
            )

            if (state.hasActiveFilters) {
                ExploreActiveFiltersRow(
                    modifier = Modifier.fillMaxWidth(),
                    filter = state.filter,
                    filterOptions = state.filterOptions,
                    onRemoveCategory = { onExploreEvent(ExploreEvent.RemoveCategory(it)) },
                    onRemoveLanguage = { onExploreEvent(ExploreEvent.RemoveLanguage(it)) },
                    onRemoveSource = { onExploreEvent(ExploreEvent.RemoveSource(it)) },
                    onClearDateRange = { onExploreEvent(ExploreEvent.ClearDateRange) },
                    onResetSort = { onExploreEvent(ExploreEvent.ChangeSort("freshness")) },
                    onClearAll = { onExploreEvent(ExploreEvent.ClearAllFilters) },
                )
            }

            when {
                refreshState is LoadState.Loading && posts.itemCount == 0 -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .weight(1f),
                        contentAlignment = Alignment.Center,
                    ) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                    }
                }

                refreshState is LoadState.Error && posts.itemCount == 0 -> {
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
                                text = refreshState.error.localizedMessage
                                    ?: stringResource(R.string.home_load_error),
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

                posts.itemCount == 0 -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .weight(1f)
                            .padding(16.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            text = stringResource(R.string.home_empty),
                            style = MaterialTheme.typography.bodyLarge,
                            textAlign = TextAlign.Center,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        )
                    }
                }

                else -> {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxSize()
                            .weight(1f),
                    ) {
                        items(
                            count = posts.itemCount,
                            key = { index -> posts.peek(index)?.id ?: "explore_$index" },
                        ) { index ->
                            val post = posts[index] ?: return@items
                            PostRow(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp),
                                title = post.title,
                                source = post.source,
                                onClick = {
                                    if (post.hasContent) {
                                        onNavigationEvent(MainNavigationEvent.ShowPostDetails(post.id))
                                    } else {
                                        onNavigationEvent(MainNavigationEvent.OpenCustomTab(post.url))
                                    }
                                },
                            )
                            HorizontalDivider(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(top = 4.dp, bottom = 4.dp),
                                thickness = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f),
                            )
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
    @PreviewParameter(ExploreStateProvider::class) previewContent: Pair<ExploreState, Flow<PagingData<Post>>>,
) {

    val (exploreState, content) = previewContent

    BrieflyTheme {
        Surface {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = { TopAppBar(onMenuSelect = {}) {} },
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
