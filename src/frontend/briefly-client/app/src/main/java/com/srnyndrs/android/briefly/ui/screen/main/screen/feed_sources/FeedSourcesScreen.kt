package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.CheckBadge
import com.composables.icons.heroicons.solid.Photo
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.SearchTextField
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.preview.FeedSourcesStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun FeedSourcesScreen(
    modifier: Modifier = Modifier,
    state: FeedSourcesState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onEvent: (FeedSourcesEvent) -> Unit,
) {

    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(space = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
        ) {
            SearchTextField(
                modifier = Modifier.weight(weight = 1f),
                value = state.searchText,
                onValueChange = { onEvent(FeedSourcesEvent.UpdateSearchText(text = it)) },
                placeholder = stringResource(id = R.string.feed_sources_search_placeholder),
                onSearch = { onEvent(FeedSourcesEvent.SearchFeedSource) },
            )
        }
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = stringResource(id = R.string.feed_sources_results),
            style = MaterialTheme.typography.bodyMedium,
        )
        UiStateContainer(
            modifier = Modifier.fillMaxSize(),
            state = state.results,
            loading = {
                ShimmerGroup {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(space = 22.dp),
                    ) {
                        items(count = 3) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(height = 64.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
                            ) {
                                ShimmerItem(
                                    modifier = Modifier.size(size = 64.dp),
                                    isLoading = true,
                                    cornerRadius = 5.dp,
                                ) {}
                                Column(
                                    modifier = Modifier.fillMaxSize(),
                                    verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                                ) {
                                    repeat(times = 2) {
                                        ShimmerItem(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .defaultMinSize(minHeight = 28.dp),
                                            isLoading = true,
                                            cornerRadius = 5.dp,
                                        ) {}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            error = {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                ) {
                    Text(
                        text = stringResource(id = R.string.feed_sources_load_error),
                        color = MaterialTheme.colorScheme.error,
                    )
                    Button(onClick = { onEvent(FeedSourcesEvent.RetrySearch) }) {
                        Text(text = stringResource(id = R.string.session_retry))
                    }
                }
            },
            success = { data ->
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(space = 22.dp),
                ) {
                    if (state.isRefreshing) {
                        item(key = "refresh_loading") {
                            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                        }
                    }
                    if (state.refreshError != null) {
                        item(key = "refresh_error") {
                            Column(verticalArrangement = Arrangement.spacedBy(space = 8.dp)) {
                                Text(
                                    text = stringResource(id = R.string.feed_sources_load_error),
                                    color = MaterialTheme.colorScheme.error,
                                )
                                Button(onClick = { onEvent(FeedSourcesEvent.RetrySearch) }) {
                                    Text(text = stringResource(id = R.string.session_retry))
                                }
                            }
                        }
                    }
                    if (data.isEmpty()) {
                        item {
                            Text(
                                modifier = Modifier.fillMaxWidth(),
                                text = stringResource(id = R.string.feed_sources_empty),
                            )
                        }
                    } else {
                        items(
                            items = data,
                            key = { it.id },
                        ) { feedSource ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(height = 64.dp)
                                    .clickable {
                                        onNavigationEvent(
                                            MainNavigationEvent.ShowSourceDetails(sourceId = feedSource.id),
                                        )
                                    },
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Row(
                                    modifier = Modifier.weight(weight = 0.8f),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
                                ) {
                                    Box(
                                        modifier = Modifier.size(size = 64.dp),
                                        contentAlignment = Alignment.Center,
                                    ) {
                                        if (feedSource.faviconUrl != null) {
                                            RemoteImageContainer(
                                                modifier = Modifier.fillMaxSize(),
                                                imageUrl = feedSource.faviconUrl,
                                                contentDescription = null,
                                                contentScale = ContentScale.Fit,
                                            )
                                        } else {
                                            Icon(
                                                modifier = Modifier.size(size = 64.dp),
                                                imageVector = Heroicons.Solid.Photo,
                                                contentDescription = null,
                                            )
                                        }
                                    }
                                    Column(verticalArrangement = Arrangement.spacedBy(space = 3.dp)) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.spacedBy(space = 4.dp),
                                            verticalAlignment = Alignment.CenterVertically,
                                        ) {
                                            Text(
                                                modifier = Modifier.weight(weight = 1f),
                                                text = feedSource.title,
                                                minLines = 1,
                                                maxLines = 1,
                                                overflow = TextOverflow.Ellipsis,
                                                style = MaterialTheme.typography.bodyLarge.copy(
                                                    fontSize = 20.sp,
                                                    fontWeight = FontWeight.Medium,
                                                ),
                                            )
                                            if (feedSource.verified) {
                                                Icon(
                                                    modifier = Modifier.size(size = 22.dp),
                                                    imageVector = Heroicons.Outline.CheckBadge,
                                                    tint = MaterialTheme.colorScheme.primary,
                                                    contentDescription = stringResource(id = R.string.feed_sources_verified),
                                                )
                                            }
                                        }
                                        Text(
                                            modifier = Modifier.fillMaxWidth(),
                                            text = feedSource.url,
                                            minLines = 1,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            style = MaterialTheme.typography.labelLarge,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            },
        )
    }
}

@PreviewLightDark
@Composable
fun FeedSourcesScreenPreview(
    @PreviewParameter(FeedSourcesStateProvider::class) state: FeedSourcesState,
) {
    BrieflyTheme {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = { TopAppBar(onMenuSelect = {}) },
        ) { paddingValues ->
            FeedSourcesScreen(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(all = 6.dp),
                state = state,
                onNavigationEvent = {},
                onEvent = {},
            )
        }
    }
}
