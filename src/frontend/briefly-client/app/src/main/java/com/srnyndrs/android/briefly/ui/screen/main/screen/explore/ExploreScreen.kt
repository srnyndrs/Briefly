package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.paging.compose.collectAsLazyPagingItems
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent

@Composable
fun ExploreScreen(
    modifier: Modifier = Modifier,
    viewModel: ExploreViewModel,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
) {
    var query by rememberSaveable { mutableStateOf("") }
    val posts = viewModel.posts.collectAsLazyPagingItems()
    Column(modifier = modifier.padding(12.dp)) {
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = query,
            onValueChange = { query = it },
            label = { Text("Search posts") },
            singleLine = true,
        )
        Button(onClick = { viewModel.onEvent(ExploreEvent.SubmitQuery(query)) }) {
            Text("Search")
        }
        PostPagingList(posts = posts, onNavigationEvent = onNavigationEvent)
    }
}

@Composable
private fun PostPagingList(
    posts: androidx.paging.compose.LazyPagingItems<Post>,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
) {
    androidx.compose.foundation.lazy.LazyColumn(modifier = Modifier.fillMaxSize()) {
        items(posts.itemCount) { index ->
            posts[index]?.let { post ->
                PostRow(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
                    title = post.title,
                    source = post.source,
                ) { onNavigationEvent(MainNavigationEvent.ShowPostDetails(post.id)) }
            }
        }
    }
}
