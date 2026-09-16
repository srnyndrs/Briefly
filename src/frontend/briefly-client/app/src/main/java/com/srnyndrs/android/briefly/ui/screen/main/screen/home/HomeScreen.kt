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
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
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
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.components.HomeCategorySelector
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.components.HomeHeadlinePager
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.preview.HomeStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.Flow
import kotlin.time.ExperimentalTime

@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    posts: LazyPagingItems<Post>,
    state: HomeState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onHomeEvent: (HomeEvent) -> Unit,
) {

    val refreshState = posts.loadState.refresh

    when {
        refreshState is LoadState.Loading && state.headlines.isEmpty() -> {
            Column(
                modifier = Modifier.then(modifier)
                    .padding(horizontal = 8.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(16f / 9)
                        .background(MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f))
                        .border(1.dp, MaterialTheme.colorScheme.onSurface, RectangleShape),
                    isLoading = true,
                    contentAlignment = Alignment.BottomCenter,
                ) {}
                repeat(3) {
                    ShimmerItem(
                        modifier = Modifier
                            .fillMaxWidth()
                            .defaultMinSize(minHeight = 42.dp),
                        isLoading = true,
                        cornerRadius = 3.dp,
                    ) {}
                }
            }
        }

        refreshState is LoadState.Error && state.headlines.isEmpty() -> {
            Box(
                modifier = modifier
                    .padding(16.dp),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        text = refreshState.error.localizedMessage ?: stringResource(R.string.home_load_error),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.error,
                        textAlign = TextAlign.Center,
                    )
                    Button(onClick = posts::retry) {
                        Text(
                            text = stringResource(R.string.home_retry)
                        )
                    }
                }
            }
        }

        state.headlines.isEmpty() &&
            posts.itemCount == 0 &&
            state.selectedCategory == null -> {
            Box(
                modifier = modifier
                    .padding(16.dp),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        text = stringResource(R.string.home_empty),
                        style = MaterialTheme.typography.bodyLarge,
                        textAlign = TextAlign.Center,
                    )
                    OutlinedButton(onClick = posts::refresh) {
                        Text(
                            text = stringResource(R.string.home_refresh)
                        )
                    }
                }
            }
        }

        else -> {
            LazyColumn(
                modifier = modifier.padding(horizontal = 8.dp),
                verticalArrangement = Arrangement.spacedBy(0.dp),
            ) {
                if (state.headlines.isNotEmpty()) {
                    item(key = "headlines") {
                        HomeHeadlinePager(
                            modifier = Modifier.fillMaxWidth(),
                            headlines = state.headlines,
                            onHeadlineSelected = { post ->
                                onNavigationEvent(
                                    MainNavigationEvent.ShowPostDetails(post.id),
                                )
                            },
                        )
                    }
                }

                if (state.categories.isNotEmpty()) {
                    item(key = "categories") {
                        HomeCategorySelector(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 18.dp),
                            categories = state.categories,
                            selectedCategory = state.selectedCategory,
                            onCategorySelected = {
                                onHomeEvent(HomeEvent.SelectCategory(it))
                            },
                        )
                    }
                }

                when {
                    refreshState is LoadState.Loading && state.headlines.isNotEmpty() -> {
                        item(key = "content_loading") {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 16.dp),
                                contentAlignment = Alignment.Center,
                            ) {
                                CircularProgressIndicator(
                                    color = MaterialTheme.colorScheme.primary,
                                )
                            }
                        }
                    }

                    refreshState is LoadState.Error && state.headlines.isNotEmpty() -> {
                        item(key = "content_error") {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(16.dp),
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                Text(
                                    text = refreshState.error.localizedMessage ?: stringResource(R.string.home_load_error),
                                    color = MaterialTheme.colorScheme.error,
                                    textAlign = TextAlign.Center,
                                )
                                OutlinedButton(onClick = posts::retry) {
                                    Text(
                                        text = stringResource(R.string.home_retry)
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
                                text = stringResource(R.string.home_content_empty),
                                style = MaterialTheme.typography.bodyLarge,
                                textAlign = TextAlign.Center,
                            )
                        }
                    }

                    else -> Unit
                }

                items(
                    count = posts.itemCount,
                    key = { index -> posts.peek(index)?.id ?: "article_$index" },
                ) { index ->
                    val article = posts[index] ?: return@items
                    PostRow(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 12.dp),
                        title = article.title,
                        source = article.source,
                        onClick = {
                            onNavigationEvent(
                                if (article.hasContent) {
                                    MainNavigationEvent.ShowPostDetails(article.id)
                                } else {
                                    MainNavigationEvent.OpenCustomTab(article.url)
                                },
                            )
                        },
                    )
                    HorizontalDivider(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 4.dp, bottom = 12.dp),
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f),
                    )
                }

                when (val appendState = posts.loadState.append) {
                    is LoadState.Loading -> item(key = "append_loading") {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp),
                            contentAlignment = Alignment.Center,
                        ) {
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                LinearProgressIndicator(
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Text(
                                    text = "Loading items...", // TODO: extract string
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                        }
                    }

                    is LoadState.Error -> item(key = "append_error") {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text(
                                text = appendState.error.localizedMessage ?: stringResource(R.string.home_append_error),
                                color = MaterialTheme.colorScheme.error,
                                textAlign = TextAlign.Center,
                            )
                            OutlinedButton(onClick = posts::retry) {
                                Text(
                                    text = stringResource(R.string.home_retry)
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

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun HomeScreenPreview(
    @PreviewParameter(HomeStateProvider::class) previewContent: Pair<HomeState, Flow<PagingData<Post>>>,
) {

    val (homeState, content) = previewContent

    BrieflyTheme {
        Surface {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = { TopAppBar(onMenuSelect = {}) {} },
            ) { paddingValues ->
                HomeScreen(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    posts = content.collectAsLazyPagingItems(),
                    state = homeState,
                    onNavigationEvent = {}
                ) {}
            }
        }
    }
}
