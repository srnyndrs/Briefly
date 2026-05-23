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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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
        modifier = Modifier.then(modifier)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 8.dp),
        verticalArrangement = Arrangement.spacedBy(0.dp)
    ) {
        // Headline
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
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .aspectRatio(16f / 9)
                                .padding(bottom = 12.dp)
                                .background(
                                    MaterialTheme.colorScheme.onSurface.copy(0.4f)
                                )
                                .border(
                                    1.dp,
                                    MaterialTheme.colorScheme.onSurface,
                                    RectangleShape
                                ),
                            isLoading = isLoading,
                            contentAlignment = Alignment.BottomCenter,
                        ) {
                            article?.imageUrl?.let { imageUrl ->
                                RemoteImageContainer(
                                    modifier = Modifier.fillMaxSize(),
                                    imageUrl = imageUrl
                                )
                            }
                        }
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalAlignment = Alignment.Start,
                            verticalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            // Source
                            ShimmerItem(
                                modifier = Modifier
                                    .defaultMinSize(minHeight = 24.dp, minWidth = 42.dp),
                                isLoading = isLoading,
                                cornerRadius = 3.dp
                            ) {
                                Text(
                                    modifier = Modifier.fillMaxWidth(),
                                    text = article?.source ?: "",
                                    style = MaterialTheme.typography.labelLarge,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    textAlign = TextAlign.Start
                                )
                            }
                            // Title
                            ShimmerItem(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .defaultMinSize(minHeight = 42.dp),
                                isLoading = isLoading,
                                cornerRadius = 3.dp
                            ) {
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
                            }
                            // Description
                            if(isLoading) {
                                Column(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalArrangement = Arrangement.spacedBy(1.dp)
                                ) {
                                    repeat(4) {
                                        ShimmerItem(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .requiredHeight(12.dp)
                                                .padding(vertical = 3.dp),
                                            isLoading = true,
                                            cornerRadius = 3.dp
                                        ) {}
                                    }
                                }
                            } else {
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
            UiStateContainer(
                modifier = Modifier.fillMaxSize(),
                state = state.result
            ) { data, isLoading ->
                Column(
                    modifier = Modifier.fillMaxSize()
                ) {
                    // Category selectors
                    LazyRow(
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
                            ShimmerItem(
                                modifier = Modifier,
                                isLoading = isLoading,
                                cornerRadius = 24.dp
                            ) {
                                Box(
                                    modifier = Modifier
                                        .wrapContentSize()
                                        .clip(RoundedCornerShape(24.dp))
                                        .border(
                                            1.dp,
                                            if (isLoading) Color.Transparent else MaterialTheme.colorScheme.onSurface,
                                            RoundedCornerShape(24.dp)
                                        )
                                        .background(
                                            if (!selected || isLoading) {
                                                MaterialTheme.colorScheme.surface
                                            } else {
                                                MaterialTheme.colorScheme.onSurface.copy(0.2f)
                                            }
                                        )
                                        .clickable(enabled = !isLoading) {
                                            selectedCategoryIndex = index
                                        }
                                        .padding(vertical = 8.dp, horizontal = 12.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        text = options[index],
                                        style = MaterialTheme.typography.bodyLarge,
                                        color = if (isLoading) Color.Transparent else MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                        }
                    }
                    // Articles
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        if (isLoading) {
                            repeat(3) {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 12.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    ShimmerItem(
                                        modifier = Modifier.defaultMinSize(minWidth = 60.dp, minHeight = 20.dp),
                                        isLoading = true,
                                        cornerRadius = 3.dp
                                    ) {}
                                    ShimmerItem(
                                        modifier = Modifier.fillMaxWidth().defaultMinSize(minHeight = 42.dp),
                                        isLoading = true,
                                        cornerRadius = 3.dp
                                    ) {}
                                }
                                HorizontalDivider(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(top = 4.dp, bottom = 12.dp),
                                    thickness = 1.dp,
                                    color = MaterialTheme.colorScheme.onSurface.copy(0.4f)
                                )
                            }
                        } else {
                            data!!.items.drop(numberOfHeadliners).forEach { article ->
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
                                        onNavigationEvent(
                                            ContentNavigationEvent.ShowArticleDetails(
                                                article.id
                                            )
                                        )
                                    } else {
                                        onNavigationEvent(
                                            ContentNavigationEvent.OpenCustomTab(
                                                article.url
                                            )
                                        )
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
