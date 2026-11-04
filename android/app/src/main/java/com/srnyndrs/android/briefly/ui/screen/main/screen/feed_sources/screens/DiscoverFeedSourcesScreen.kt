package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.screens

import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.components.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.*
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.*
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun DiscoverFeedSourcesScreen(
    modifier: Modifier = Modifier,
    state: DiscoverFeedSourcesState,
    onEvent: (FeedSourcesEvent) -> Unit,
) {
    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(space = 24.dp),
    ) {
        SearchTextField(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 18.dp),
            value = state.url,
            onValueChange = { onEvent(FeedSourcesEvent.UpdateDiscoveryUrl(url = it)) },
            placeholder = stringResource(id = R.string.feed_sources_url),
            onSearch = { onEvent(FeedSourcesEvent.Discover) },
        )
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = stringResource(id = R.string.feed_sources_results),
            style = MaterialTheme.typography.bodyMedium,
        )
        UiStateContainer(
            modifier = Modifier.fillMaxSize(),
            state = state.results,
            idle = { Text(text = stringResource(id = R.string.feed_sources_discovery_hint)) },
            loading = {
                FeedSourceResultsPlaceholder()
            },
            error = {
                Column {
                    Text(text = stringResource(id = R.string.feed_sources_load_error))
                    Button(onClick = { onEvent(FeedSourcesEvent.RetryDiscovery) }) {
                        Text(text = stringResource(id = R.string.session_retry))
                    }
                }
            },
            success = { candidates ->
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(space = 22.dp),
                ) {
                    if (state.isRefreshing) {
                        item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
                    }
                    if (state.refreshFailed) {
                        item {
                            TextButton(onClick = { onEvent(FeedSourcesEvent.RetryDiscovery) }) {
                                Text(text = stringResource(id = R.string.feed_sources_retry_discovery))
                            }
                        }
                    }
                    if (candidates.isEmpty()) {
                        item { Text(text = stringResource(id = R.string.feed_sources_discovery_empty)) }
                    }
                    items(
                        items = candidates,
                        key = { it.url },
                    ) { candidate ->
                        FeedSourceResultItem(
                            title = candidate.title,
                            url = candidate.url,
                            faviconUrl = candidate.faviconUrl,
                            onClick = { onEvent(FeedSourcesEvent.SelectDiscoverySource(url = candidate.url)) },
                        )
                    }
                }
            },
        )
    }
    state.selectedSource?.let { source ->
        DiscoverySourceDialog(
            source = source,
            addition = state.additions[source.url] ?: UiState.Idle,
            isDuplicate = source.url in state.duplicateUrls,
            onUpdate = { onEvent(FeedSourcesEvent.UpdateDiscoverySource(source = it)) },
            onDismiss = { onEvent(FeedSourcesEvent.DismissDiscoverySource) },
            onAdd = { onEvent(FeedSourcesEvent.AddSource(url = source.url)) },

        )
    }
}

@PreviewLightDark
@Composable
private fun DiscoverFeedSourcesScreenPreview() {
    BrieflyTheme {
        Surface {
            DiscoverFeedSourcesScreen(
                state = DiscoverFeedSourcesState(
                    url = "https://telex.hu",
                    results = UiState.Success(data = listOf(
                        com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult(
                            url = "https://telex.hu/rss",
                            title = "Telex.hu",
                            description = "Latest news from Telex.",
                        ),
                    )),
                ),
                onEvent = {},
            )
        }
    }
}
