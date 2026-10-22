package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
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
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.components.HomeArticlePlaceholder
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.components.HomeCategorySelector
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.components.HomeHeadlinePager
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.preview.HomeStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.Flow

@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    posts: LazyPagingItems<HomeArticle>,
    state: HomeState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onHomeEvent: (HomeEvent) -> Unit,
) {

    val refreshState = posts.loadState.refresh
    val hasCurrentArticles = posts.itemCount > 0 &&
        posts.peek(index = 0)?.category == state.selectedCategory
    val awaitingCategory = posts.itemCount > 0 && !hasCurrentArticles
    val isLoading = refreshState is LoadState.Loading ||
        (refreshState !is LoadState.Error && (awaitingCategory || state.categories == null))

    when {
        isLoading && state.categories == null -> {
            ShimmerGroup {
                Column(
                    modifier = Modifier
                        .then(modifier)
                        .verticalScroll(state = rememberScrollState())
                        .padding(horizontal = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                ) {
                    ShimmerItem(
                        modifier = Modifier
                            .fillMaxWidth()
                            .aspectRatio(ratio = 16f / 9)
                            .background(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f))
                            .border(
                                width = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface,
                                shape = RectangleShape,
                            ),
                        isLoading = true,
                        contentAlignment = Alignment.BottomCenter,
                    ) {}
                    repeat(times = 3) {
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .defaultMinSize(minHeight = 42.dp),
                            isLoading = true,
                            cornerRadius = 3.dp,
                        ) {}
                    }
                    repeat(times = 3) {
                        HomeArticlePlaceholder(modifier = Modifier.fillMaxWidth())
                    }
                }
            }
        }

        refreshState is LoadState.Error && state.categories == null -> {
            Box(
                modifier = Modifier
                    .then(modifier)
                    .padding(all = 16.dp),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                ) {
                    Text(
                        text = stringResource(id = R.string.home_load_error),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.error,
                        textAlign = TextAlign.Center,
                    )
                    Button(onClick = posts::retry) {
                        Text(
                            text = stringResource(id = R.string.home_retry),
                        )
                    }
                }
            }
        }

        state.headlines.isEmpty() &&
            !hasCurrentArticles &&
            !isLoading &&
            refreshState is LoadState.NotLoading &&
            state.selectedCategory == null -> {
            Box(
                modifier = Modifier
                    .then(modifier)
                    .padding(all = 16.dp),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                ) {
                    Text(
                        text = stringResource(id = R.string.home_empty),
                        style = MaterialTheme.typography.bodyLarge,
                        textAlign = TextAlign.Center,
                    )
                    OutlinedButton(onClick = posts::refresh) {
                        Text(
                            text = stringResource(id = R.string.home_refresh),
                        )
                    }
                }
            }
        }

        else -> {
            LazyColumn(
                modifier = Modifier
                    .then(modifier)
                    .padding(
                        start = 8.dp,
                        end = 8.dp,
                        top = 6.dp,
                    ),
                verticalArrangement = Arrangement.spacedBy(space = 0.dp),
            ) {
                if (state.headlines.isNotEmpty()) {
                    item(key = "headlines") {
                        HomeHeadlinePager(
                            modifier = Modifier.fillMaxWidth(),
                            headlines = state.headlines,
                            onHeadlineSelected = { post ->
                                if (post.hasContent) {
                                    onNavigationEvent(MainNavigationEvent.ShowPostDetails(postId = post.id))
                                } else {
                                    onNavigationEvent(MainNavigationEvent.OpenCustomTab(url = post.url))
                                }
                            },
                        )
                    }
                }

                if (state.categories.orEmpty().isNotEmpty()) {
                    item(key = "categories") {
                        HomeCategorySelector(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 18.dp),
                            categories = state.categories ?: emptyList(),
                            selectedCategory = state.selectedCategory,
                            onCategorySelected = {
                                onHomeEvent(HomeEvent.SelectCategory(category = it))
                            },
                        )
                    }
                }

                when {
                    isLoading && !hasCurrentArticles -> {
                        item(key = "content_loading") {
                            ShimmerGroup {
                                Column(modifier = Modifier.fillMaxWidth()) {
                                    repeat(times = 3) {
                                        HomeArticlePlaceholder(modifier = Modifier.fillMaxWidth())
                                    }
                                }
                            }
                        }
                    }

                    isLoading -> {
                        item(key = "content_loading") {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 16.dp),
                                contentAlignment = Alignment.Center,
                            ) {
                                LinearProgressIndicator(
                                    modifier = Modifier.fillMaxWidth(),
                                )
                            }
                        }
                    }

                    refreshState is LoadState.Error -> {
                        item(key = "content_error") {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(all = 16.dp),
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                            ) {
                                Text(
                                    text = stringResource(id = R.string.home_load_error),
                                    color = MaterialTheme.colorScheme.error,
                                    textAlign = TextAlign.Center,
                                )
                                OutlinedButton(onClick = posts::retry) {
                                    Text(
                                        text = stringResource(id = R.string.home_retry),
                                    )
                                }
                            }
                        }
                    }

                    posts.itemCount == 0 && state.selectedCategory != null -> {
                        item(key = "content_empty") {
                            Text(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 24.dp),
                                text = stringResource(id = R.string.home_content_empty),
                                style = MaterialTheme.typography.bodyLarge,
                                textAlign = TextAlign.Center,
                            )
                        }
                    }

                    else -> Unit
                }

                items(
                    count = if (hasCurrentArticles) posts.itemCount else 0,
                    key = { index -> posts.peek(index = index)?.post?.id ?: "article_$index" },
                ) { index ->
                    val article = posts[index]?.post ?: return@items
                    PostRow(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 12.dp),
                        title = article.title,
                        source = article.sourceTitle,
                        onClick = {
                            onNavigationEvent(
                                if (article.hasContent) {
                                    MainNavigationEvent.ShowPostDetails(postId = article.id)
                                } else {
                                    MainNavigationEvent.OpenCustomTab(url = article.url)
                                },
                            )
                        },
                    )
                    HorizontalDivider(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(
                                top = 4.dp,
                                bottom = 12.dp,
                            ),
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f),
                    )
                }

                when (
                    val appendState = posts.loadState.append.takeUnless {
                        isLoading || !hasCurrentArticles
                    }
                ) {
                    is LoadState.Loading -> item(key = "append_loading") {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp),
                            contentAlignment = Alignment.Center,
                        ) {
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                            ) {
                                LinearProgressIndicator(
                                    modifier = Modifier.fillMaxWidth(),
                                )
                                Text(
                                    text = stringResource(id = R.string.home_loading_items),
                                    style = MaterialTheme.typography.bodyMedium,
                                )
                            }
                        }
                    }

                    is LoadState.Error -> item(key = "append_error") {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(all = 16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                        ) {
                            Text(
                                text = stringResource(id = R.string.home_append_error),
                                color = MaterialTheme.colorScheme.error,
                                textAlign = TextAlign.Center,
                            )
                            OutlinedButton(onClick = posts::retry) {
                                Text(
                                    text = stringResource(id = R.string.home_retry),
                                )
                            }
                        }
                    }

                    else -> Unit
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun HomeScreenPreview(
    @PreviewParameter(HomeStateProvider::class) previewContent: Pair<HomeState, Flow<PagingData<HomeArticle>>>,
) {

    val (homeState, content) = previewContent

    BrieflyTheme {
        Surface {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = { TopAppBar(onMenuSelect = {}) },
            ) { paddingValues ->
                HomeScreen(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    posts = content.collectAsLazyPagingItems(),
                    state = homeState,
                    onNavigationEvent = {},
                ) {}
            }
        }
    }
}
