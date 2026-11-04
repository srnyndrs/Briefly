package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SecondaryTabRow
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.screens.DiscoverFeedSourcesScreen
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.screens.SearchFeedSourcesScreen
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedSourcesScreen(
    modifier: Modifier = Modifier,
    state: FeedSourcesState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onEvent: (FeedSourcesEvent) -> Unit,
) {
    var selectedTab by rememberSaveable { mutableIntStateOf(0) }
    Column(modifier = Modifier.then(modifier)) {
        SecondaryTabRow(selectedTabIndex = selectedTab) {
            listOf(R.string.search, R.string.feed_sources_discover).forEachIndexed { index, title ->
                Tab(
                    selected = selectedTab == index,
                    onClick = { selectedTab = index },
                    text = { Text(text = stringResource(id = title)) },
                )
            }
        }
        if (selectedTab == 0) {
            SearchFeedSourcesScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onNavigationEvent = onNavigationEvent,
                onEvent = onEvent,
            )
        } else {
            DiscoverFeedSourcesScreen(
                modifier = Modifier.fillMaxSize(),
                state = state.discovery,
                onEvent = onEvent,
            )
        }
    }
}

@PreviewLightDark
@Composable
private fun FeedSourcesScreenPreview() {
    BrieflyTheme {
        Surface {
            FeedSourcesScreen(
                state = FeedSourcesState(),
                onNavigationEvent = {},
                onEvent = {},
            )
        }
    }
}
