package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search

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
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Heart
import com.composables.icons.heroicons.solid.Heart
import com.composables.icons.heroicons.solid.Photo
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.SearchTextField
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.common.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search.preview.FeedSearchStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun FeedSearchScreen(
    modifier: Modifier = Modifier,
    state: FeedSearchState,
    onNavigationEvent: (ContentNavigationEvent) -> Unit,
    onEvent: (FeedSearchEvent) -> Unit
) {

    val (searchText, setSearchText) = remember { mutableStateOf("") }

    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Search
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            SearchTextField(
                modifier = Modifier.weight(1f),
                value = searchText,
                onValueChange = setSearchText,
                placeholder = "Search feeds",
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
        UiStateContainer(
            modifier = Modifier.fillMaxSize(),
            state = state.results
        ) { data, isLoading ->
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(22.dp)
            ) {
                if(isLoading) {
                    items(3) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(64.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            // Image
                            ShimmerItem(
                                modifier = Modifier.size(64.dp),
                                isLoading = true,
                                cornerRadius = 5.dp
                            ) {}
                            // Text
                            Column(
                                modifier = Modifier.fillMaxSize(),
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                // Title
                                ShimmerItem(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .defaultMinSize(minHeight = 28.dp),
                                    isLoading = true,
                                    cornerRadius = 5.dp
                                ) {}
                                // URL
                                ShimmerItem(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .defaultMinSize(minHeight = 28.dp),
                                    isLoading = true,
                                    cornerRadius = 5.dp
                                ) {}
                            }
                        }
                    }
                } else {
                    if(data?.isEmpty() == true) {
                        item {
                            Text(
                                modifier = Modifier.fillMaxWidth(),
                                text = "No results found for this query"
                            )
                        }
                    } else {
                        items(data!!) { feedSource ->
                            val favourite = feedSource.isSubscribed
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(56.dp)
                                    .clickable {
                                        onNavigationEvent(ContentNavigationEvent.ShowFeedDetails((feedSource.id)))
                                    },
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(
                                    modifier = Modifier.weight(0.8f),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    // Image
                                    Box(
                                        modifier = Modifier.size(64.dp),
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
                                            modifier = Modifier.size(64.dp),
                                            imageVector = Heroicons.Solid.Photo,
                                            contentDescription = null
                                        )
                                    }
                                    // Text
                                    Column(
                                        verticalArrangement = Arrangement.spacedBy(3.dp),
                                    ) {
                                        // Title
                                        Text(
                                            modifier = Modifier.fillMaxWidth(),
                                            text = feedSource.title,
                                            minLines = 1,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            style = MaterialTheme.typography.bodyLarge.copy(
                                                fontSize = 20.sp,
                                                fontWeight = FontWeight.Medium
                                            )
                                        )
                                        // URL
                                        Text(
                                            modifier = Modifier.fillMaxWidth(),
                                            text = feedSource.url,
                                            minLines = 1,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            style = MaterialTheme.typography.labelLarge
                                        )
                                    }
                                }
                                Row(
                                    modifier = Modifier.weight(0.15f),
                                    horizontalArrangement = Arrangement.End,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
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
                                            modifier = Modifier.size(36.dp),
                                            imageVector =
                                                if(!favourite) {
                                                    Heroicons.Outline.Heart
                                                } else {
                                                    Heroicons.Solid.Heart
                                                },
                                            contentDescription = null
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun FeedSearchScreenPreview(
    @PreviewParameter(FeedSearchStateProvider::class) state: FeedSearchState
) {
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
                state = state,
                onNavigationEvent = {}
            ) {

            }
        }
    }
}
