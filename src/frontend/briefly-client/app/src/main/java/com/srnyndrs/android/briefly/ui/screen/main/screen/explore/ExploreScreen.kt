package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.paging.PagingData
import androidx.paging.compose.LazyPagingItems
import androidx.paging.compose.collectAsLazyPagingItems
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview.ExploreStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.Flow

@Composable
fun ExploreScreen(
    modifier: Modifier = Modifier,
    posts: LazyPagingItems<Post>,
    state: ExploreState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onExploreEvent: (ExploreEvent) -> Unit,
) {

    Column(
        modifier = Modifier.then(modifier)
            .padding(horizontal = 12.dp)
    ) {
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = state.query,
            onValueChange = { query -> onExploreEvent(ExploreEvent.UpdateQuery(query)) },
            label = {
                Text(
                    text = stringResource(R.string.explore_search_posts),
                )
            },
            singleLine = true,
        )
        Button(
            onClick = {
                onExploreEvent(ExploreEvent.SubmitQuery)
            }
        ) {
            Text(
                text = stringResource(R.string.explore_search),
            )
        }
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
        ) {
            items(count = posts.itemCount) { index ->
                posts[index]?.let { post ->
                    PostRow(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 12.dp),
                        title = post.title,
                        source = post.source,
                    ) {
                        onNavigationEvent(MainNavigationEvent.ShowPostDetails(post.id))
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun ExploreScreenPreview(
    @PreviewParameter(ExploreStateProvider::class) previewContent: Pair<ExploreState, Flow<PagingData<Post>>>
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
                    onNavigationEvent = {}
                ) {}
            }
        }
    }
}
