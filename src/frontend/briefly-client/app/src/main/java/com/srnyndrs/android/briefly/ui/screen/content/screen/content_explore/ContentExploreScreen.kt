package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
// import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
// import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
// import androidx.compose.ui.graphics.RectangleShape
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleCard
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.preview.ContentExploreStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ContentExploreScreen(
    modifier: Modifier = Modifier,
    state: ContentExploreState,
    onArticleSelected: (String) -> Unit,
) {

    // VARIABLES
    val articles = state.result

    // CONTENT
    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // List
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Headline
            item {
                // Headline Card
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    //verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    // Optional Image
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .aspectRatio(16f / 9)
                            .background(
                                MaterialTheme.colorScheme.onSurface.copy(0.4f)
                            )
                            .border(
                                1.dp,
                                MaterialTheme.colorScheme.onSurface,
                                RectangleShape
                            ),
                        contentAlignment = Alignment.Center,
                    ) {
                        Image(
                            imageVector = Icons.Default.Info,
                            contentDescription = null
                        )
                    }
                    Spacer(
                        modifier = Modifier.requiredHeight(12.dp)
                    )
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        // Title
                        Text(
                            modifier = Modifier.fillMaxWidth(),
                            text = "This is breaking news!",
                            // TODO
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.W500,
                            maxLines = 2,
                            minLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            textAlign = TextAlign.Start,
                        )
                        Spacer(
                            modifier = Modifier.requiredHeight(6.dp)
                        )
                        // Subtitle
                        Text(
                            modifier = Modifier.fillMaxWidth(),
                            text = "Lorem ipsum domeros in cantatem",
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 2,
                            minLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            textAlign = TextAlign.Justify,
                        )
                        Spacer(
                            modifier = Modifier.requiredHeight(12.dp)
                        )
                        // Source
                        Text(
                            modifier = Modifier.fillMaxWidth(),
                            text = "Telex",
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.W400,
                            maxLines = 1,
                            minLines = 1,
                            textAlign = TextAlign.Start
                        )
                    }
                }
            }
            // Divider
            item {
                HorizontalDivider(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 2.dp, bottom = 8.dp),
                    thickness = 2.dp,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
            // Articles
            when(articles) {
                is UiState.Error -> {
                    item {
                        // TODO: error presentation
                        Text(
                            text = "Error"
                        )
                    }
                }
                is UiState.Success -> {
                    items(articles.data.items) { article ->
                        ArticleCard(
                            title = article.title,
                            description = article.description,
                            imageUrl = article.imageUrl,
                            // TODO: add source
                            source = null
                        ) {
                            onArticleSelected(article.id)
                        }
                    }
                }
                else -> {
                    // TODO: Loading state
                    item {
                        LinearProgressIndicator()
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun ContentExplorePreview(
    @PreviewParameter(ContentExploreStateProvider::class) state: ContentExploreState
) {
    BrieflyTheme {
        Surface {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = {
                    TopAppBar(
                        onMenuSelect = {}
                    ) {}
                }
            ) { paddingValues ->
                ContentExploreScreen(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .padding(top = 12.dp),
                    state = state
                ) {

                }
            }
        }
    }
}
