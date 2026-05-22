package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.min
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.SearchTextField
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.common.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleRow
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.preview.ContentExploreStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.openCustomTab

@Composable
fun ContentExploreScreen(
    modifier: Modifier = Modifier,
    state: ContentExploreState,
    onNavigationEvent: (ContentNavigationEvent) -> Unit,
) {

    // VARIABLES
    val numberOfHeadliners = 3
    val articles = state.result
    val pagerState = rememberPagerState() {
        numberOfHeadliners
    }
    var query by rememberSaveable {
        mutableStateOf("")
    }
    var selectedCategoryIndex by rememberSaveable {
        mutableIntStateOf(0)
    }

    // CONTENT
    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(0.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // List
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp),
            verticalArrangement = Arrangement.spacedBy(0.dp)
        ) {
            // Headline
            item {
                UiStateContainer(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(356.dp),
                    state = state.result
                ) { data, isLoading ->
                    HorizontalPager(
                        modifier = Modifier.fillMaxSize(),
                        state = pagerState,
                        pageSpacing = 12.dp
                    ) { page ->

                        val article = data?.items?.getOrNull(page)
                        if(data?.items?.isEmpty() == true) {
                            return@HorizontalPager
                        }
                        // Headline Card
                        ShimmerItem(
                            modifier = Modifier.fillMaxSize(),
                            isLoading = isLoading
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .clickable {
                                        article?.id?.let {
                                            onNavigationEvent(ContentNavigationEvent.ShowArticleDetails(it))
                                        }
                                    },
                                verticalArrangement = Arrangement.Top
                            ) {
                                // Optional Image
                                article?.imageUrl?.let { imageUrl ->
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
                                        contentAlignment = Alignment.BottomCenter,
                                    ) {
                                        RemoteImageContainer(
                                            modifier = Modifier.fillMaxSize(),
                                            imageUrl = imageUrl
                                        )
                                    }
                                    Spacer(
                                        modifier = Modifier.requiredHeight(12.dp)
                                    )
                                }
                                Column(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    // Source
                                    Text(
                                        modifier = Modifier.fillMaxWidth(),
                                        text = article?.source ?: "",
                                        style = MaterialTheme.typography.labelLarge,
                                        color = MaterialTheme.colorScheme.onSurface,
                                        textAlign = TextAlign.Start
                                    )
                                    // Title
                                    Text(
                                        modifier = Modifier.fillMaxWidth(),
                                        text = article?.title ?: "",
                                        textAlign = TextAlign.Start,
                                        // TODO
                                        style = MaterialTheme.typography.titleLarge,
                                        fontWeight = FontWeight.Black,
                                        maxLines = 3,
                                        minLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                    )
                                    Text(
                                        modifier = Modifier.fillMaxWidth(),
                                        text = article?.description ?: "",
                                        textAlign = TextAlign.Start,
                                        style = MaterialTheme.typography.bodyMedium,
                                        minLines = 1,
                                        maxLines = 2,
                                        overflow = TextOverflow.Ellipsis,
                                    )
                                }
                            }
                        }
                    }
                }
                Row(
                    modifier = Modifier
                        .padding(vertical = 12.dp)
                        .fillMaxWidth()
                        .requiredHeight(32.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    val pageCount = pagerState.pageCount
                    repeat(pageCount) { iteration ->
                        val selected = pagerState.currentPage == iteration
                        HorizontalDivider(
                            modifier = Modifier.weight(1f / pageCount)
                                .clip(RoundedCornerShape(3.dp)),
                            thickness = if(selected) 3.dp else 1.dp,
                            color = MaterialTheme.colorScheme.onSurface.copy(0.8f)
                        )
                        if(pageCount - 1 > iteration) {
                            Spacer(
                                modifier = Modifier.requiredWidth(3.dp)
                            )
                        }
                    }
                }
            }
            item {
                // Category selectors
                LazyRow (
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 18.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    val options = listOf(
                        "Összes", // TODO
                        "Sport",
                        "Belföld",
                        "Külföld",
                        "Kultúra"
                    )
                    items(options.size) { index ->
                        val selected = index == selectedCategoryIndex
                        Box(
                            modifier = Modifier
                                .wrapContentSize()
                                .clip(RoundedCornerShape(24.dp))
                                .border(
                                    1.dp,
                                    MaterialTheme.colorScheme.onSurface,
                                    RoundedCornerShape(24.dp)
                                )
                                .background(
                                    if(!selected) {
                                        MaterialTheme.colorScheme.surface
                                    } else {
                                        MaterialTheme.colorScheme.onSurface.copy(0.2f)
                                    }
                                )
                                .clickable {
                                    selectedCategoryIndex = index
                                }
                                .padding(vertical = 8.dp, horizontal = 12.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = options[index],
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }

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
                    items(articles.data.items.drop(numberOfHeadliners)) { article ->
                        ArticleRow(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp),
                            title = article.title,
                            source = article.source,
                            description = article.description,
                            tag = article.category
                        ) {
                            if (article.hasContent) {
                                onNavigationEvent(ContentNavigationEvent.ShowArticleDetails(article.id))
                            } else {
                                onNavigationEvent(ContentNavigationEvent.OpenCustomTab(article.url))
                            }
                        }
                        HorizontalDivider(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 4.dp, bottom = 12.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.onSurface.copy(0.4f)
                        )
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
