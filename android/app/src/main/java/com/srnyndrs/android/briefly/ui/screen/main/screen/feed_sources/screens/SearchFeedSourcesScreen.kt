package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.screens

import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.components.FeedSourceResultItem
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.components.FeedSourceResultsPlaceholder
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.SearchTextField
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesState
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.preview.FeedSourcesStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SearchFeedSourcesScreen(
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
                FeedSourceResultsPlaceholder()
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
                            FeedSourceResultItem(
                                title = feedSource.title,
                                url = feedSource.url,
                                faviconUrl = feedSource.faviconUrl,
                                verified = feedSource.verified,
                                onClick = {
                                    onNavigationEvent(MainNavigationEvent.ShowSourceDetails(sourceId = feedSource.id))
                                },
                            )
                        }
                    }
                }
            },
        )
    }
}

@PreviewLightDark
@Composable
private fun SearchFeedSourcesScreenPreview(
    @PreviewParameter(FeedSourcesStateProvider::class) state: FeedSourcesState,
) {
    BrieflyTheme {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = { TopAppBar(onMenuSelect = {}) },
        ) { paddingValues ->
            SearchFeedSourcesScreen(
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
