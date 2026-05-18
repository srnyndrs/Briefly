package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import com.srnyndrs.android.briefly.ui.common.SearchTextField
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun FeedSearchScreen(
    modifier: Modifier = Modifier,
    state: UiState<List<FeedSourceResultItem>>,
    onEvent: (FeedSearchEvent) -> Unit
) {

    val (searchText, setSearchText) = remember { mutableStateOf("") }

    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Screen Title
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = "Explore Feeds",
            style = MaterialTheme.typography.headlineSmall,
            textAlign = TextAlign.Center
        )
        // Search
        Row(
            modifier = Modifier
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            SearchTextField(
                value = searchText,
                onValueChange = setSearchText,
                modifier = Modifier.weight(1f),
                onSearch = {
                    onEvent(FeedSearchEvent.SearchFeedSource(searchText))
                }
            )
        }
        //
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = "Results",
            style = MaterialTheme.typography.bodyMedium
        )
        // Results
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(22.dp)
        ) {
            when(state) {
                is UiState.Error -> {
                    // TODO: better error state handling
                    item {
                        Text(
                            modifier = Modifier.fillMaxWidth(),
                            text = state.message,
                            textAlign = TextAlign.Center,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
                is UiState.Loading -> {
                    item {
                        LinearProgressIndicator()
                    }
                }
                is UiState.Success -> {
                    if (state.data.isEmpty()) {
                        item {
                            Text(
                                modifier = Modifier.fillMaxWidth(),
                                text = "No results found for this query"
                            )
                        }
                    } else {
                        items(state.data) { feedSource ->
                            val favourite = feedSource.isSubscribed
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(56.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    // Image
                                    Box(
                                        modifier = Modifier
                                            .size(72.dp)
                                            .clip(RoundedCornerShape(5.dp)),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        feedSource.favicon?.let { imageUrl ->
                                            RemoteImageContainer(
                                                modifier = Modifier.fillMaxSize(),
                                                imageUrl = imageUrl,
                                                contentScale = ContentScale.Fit,
                                            )
                                        } ?:
                                        Icon(
                                            imageVector = Icons.Default.Info,
                                            contentDescription = null
                                        )
                                    }
                                    // Text
                                    Column(
                                        verticalArrangement = Arrangement.spacedBy(3.dp),
                                    ) {
                                        // Title
                                        Text(
                                            text = feedSource.title,
                                            minLines = 1,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            style = MaterialTheme.typography.titleLarge.copy(
                                                fontWeight = FontWeight.Medium
                                            )
                                        )
                                        // URL
                                        Text(
                                            text = feedSource.url,
                                            minLines = 1,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            style = MaterialTheme.typography.labelLarge
                                        )
                                    }
                                }
                                IconButton(
                                    modifier = Modifier.size(48.dp),
                                    onClick = {
                                        if(!favourite) {
                                            onEvent(FeedSearchEvent.SubscribeFeedSource(feedSource.id))
                                        } else {
                                            onEvent(FeedSearchEvent.UnsubscribeFeedSource(feedSource.id))
                                        }
                                    }
                                ) {
                                    Icon(
                                        modifier = Modifier.size(32.dp),
                                        imageVector =
                                            if(!favourite) {
                                                Icons.Default.FavoriteBorder
                                            } else {
                                                Icons.Default.Favorite
                                            },
                                        contentDescription = null
                                    )
                                }
                            }
                        }
                    }
                }
                else -> {
                    // Show nothing on IDLE
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun FeedSearchScreenPreview() {
    BrieflyTheme {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = {
                TopAppBar(
                    onMenuSelect = {}
                ) { }
            }
        ) { paddingValues ->
            FeedSearchScreen(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(6.dp),
                state = UiState.Idle
            ) {

            }
        }
    }
}
