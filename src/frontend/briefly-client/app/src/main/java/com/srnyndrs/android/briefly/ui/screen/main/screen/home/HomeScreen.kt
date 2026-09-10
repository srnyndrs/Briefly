package com.srnyndrs.android.briefly.ui.screen.main.screen.home

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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.paging.LoadState
import androidx.paging.PagingData
import androidx.paging.compose.LazyPagingItems
import androidx.paging.compose.collectAsLazyPagingItems
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.components.PostRow
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.flowOf
import kotlin.time.ExperimentalTime

@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    articles: LazyPagingItems<Post>,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
) {
    when (val refreshState = articles.loadState.refresh) {
        is LoadState.Loading -> {
            HomeLoadingSkeleton(
                modifier = modifier.padding(horizontal = 8.dp),
            )
        }
        is LoadState.Error -> {
            HomeErrorState(
                modifier = modifier.fillMaxSize().padding(16.dp),
                errorMessage = refreshState.error.localizedMessage ?: "Failed to load articles",
                onRetry = { articles.retry() }
            )
        }
        is LoadState.NotLoading -> {
            if (articles.itemCount == 0) {
                HomeEmptyState(
                    modifier = modifier.fillMaxSize().padding(16.dp),
                    onRefresh = { articles.refresh() }
                )
            } else {
                val numberOfHeadliners = minOf(3, articles.itemCount)
                val pagerState = rememberPagerState { numberOfHeadliners }

                LazyColumn(
                    modifier = Modifier
                        .then(modifier)
                        .padding(horizontal = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(0.dp)
                ) {
                    // 1. Headline section
                    item(key = "headlines") {
                        HorizontalPager(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(356.dp),
                            state = pagerState,
                            pageSpacing = 12.dp
                        ) { page ->
                            val article = articles[page]
                            if (article != null) {
                                HeadlineCard(
                                    article = article,
                                    onClick = {
                                        onNavigationEvent(
                                            MainNavigationEvent.ShowPostDetails(article.id)
                                        )
                                    }
                                )
                            }
                        }
                    }

                    // 2. Pager indicators
                    item(key = "indicators") {
                        val pageCount = pagerState.pageCount
                        Row(
                            modifier = Modifier
                                .padding(vertical = 12.dp)
                                .fillMaxWidth()
                                .requiredHeight(32.dp),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            repeat(pageCount) { iteration ->
                                val selected = pagerState.currentPage == iteration
                                HorizontalDivider(
                                    modifier = Modifier
                                        .weight(1f / pageCount)
                                        .clip(RoundedCornerShape(3.dp)),
                                    thickness = if (selected) 3.dp else 1.dp,
                                    color = MaterialTheme.colorScheme.onSurface.copy(0.8f)
                                )
                                if (pageCount - 1 > iteration) {
                                    Spacer(modifier = Modifier.requiredWidth(3.dp))
                                }
                            }
                        }
                    }

                    // 3. Paginated post items
                    val remainingCount = (articles.itemCount - numberOfHeadliners).coerceAtLeast(0)
                    items(
                        count = remainingCount,
                        key = { index -> articles.peek(index + numberOfHeadliners)?.id ?: "article_$index" }
                    ) { index ->
                        val article = articles[index + numberOfHeadliners]
                        if (article != null) {
                            PostRow(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp),
                                title = article.title,
                                source = article.source
                            ) {
                                if (article.hasContent) {
                                    onNavigationEvent(
                                        MainNavigationEvent.ShowPostDetails(article.id)
                                    )
                                } else {
                                    onNavigationEvent(
                                        MainNavigationEvent.OpenCustomTab(article.url)
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

                    // 5. Append load state (loading more or error)
                    when (val appendState = articles.loadState.append) {
                        is LoadState.Loading -> {
                            item(key = "append_loading") {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 16.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    CircularProgressIndicator(
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                        }
                        is LoadState.Error -> {
                            item(key = "append_error") {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(16.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Text(
                                        text = appendState.error.localizedMessage ?: "Failed to load more articles",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.error,
                                        textAlign = TextAlign.Center
                                    )
                                    OutlinedButton(
                                        onClick = { articles.retry() }
                                    ) {
                                        Text("Retry")
                                    }
                                }
                            }
                        }
                        else -> {}
                    }
                }
            }
        }
    }
}

@Composable
private fun HeadlineCard(
    modifier: Modifier = Modifier,
    article: Post,
    onClick: () -> Unit
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .clickable(onClick = onClick),
        verticalArrangement = Arrangement.Top
    ) {
        ShimmerItem(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9)
                .padding(bottom = 12.dp)
                .background(MaterialTheme.colorScheme.onSurface.copy(0.4f))
                .border(1.dp, MaterialTheme.colorScheme.onSurface, RectangleShape),
            isLoading = false,
            contentAlignment = Alignment.BottomCenter,
        ) {
            article.imageUrl?.let { imageUrl ->
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
            Text(
                modifier = Modifier.fillMaxWidth(),
                text = article.source ?: "",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurface,
                textAlign = TextAlign.Start
            )
            Text(
                modifier = Modifier.fillMaxWidth(),
                text = article.title,
                textAlign = TextAlign.Start,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Black,
                maxLines = 3,
                minLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                modifier = Modifier.fillMaxWidth(),
                text = article.description ?: "",
                textAlign = TextAlign.Start,
                style = MaterialTheme.typography.bodyMedium,
                minLines = 1,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun HomeLoadingSkeleton(
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(0.dp)
    ) {
        // Headline Skeleton
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .requiredHeight(356.dp),
            verticalArrangement = Arrangement.Top
        ) {
            ShimmerItem(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(16f / 9)
                    .padding(bottom = 12.dp)
                    .background(MaterialTheme.colorScheme.onSurface.copy(0.4f))
                    .border(1.dp, MaterialTheme.colorScheme.onSurface, RectangleShape),
                isLoading = true,
                contentAlignment = Alignment.BottomCenter,
            ) {}
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.Start,
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                ShimmerItem(
                    modifier = Modifier.defaultMinSize(minHeight = 24.dp, minWidth = 42.dp),
                    isLoading = true,
                    cornerRadius = 3.dp
                ) {}
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .defaultMinSize(minHeight = 42.dp),
                    isLoading = true,
                    cornerRadius = 3.dp
                ) {}
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
            }
        }

        // Indicator skeleton
        Row(
            modifier = Modifier
                .padding(vertical = 12.dp)
                .fillMaxWidth()
                .requiredHeight(32.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            repeat(3) { iteration ->
                HorizontalDivider(
                    modifier = Modifier
                        .weight(1f / 3)
                        .clip(RoundedCornerShape(3.dp)),
                    thickness = if (iteration == 0) 3.dp else 1.dp,
                    color = MaterialTheme.colorScheme.onSurface.copy(0.8f)
                )
                if (2 > iteration) {
                    Spacer(modifier = Modifier.requiredWidth(3.dp))
                }
            }
        }

        // Article rows skeleton
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
                    modifier = Modifier
                        .fillMaxWidth()
                        .defaultMinSize(minHeight = 42.dp),
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
    }
}

@Composable
private fun HomeErrorState(
    modifier: Modifier = Modifier,
    errorMessage: String,
    onRetry: () -> Unit
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = errorMessage,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.error,
                textAlign = TextAlign.Center
            )
            Button(onClick = onRetry) {
                Text("Retry")
            }
        }
    }
}

@Composable
private fun HomeEmptyState(
    modifier: Modifier = Modifier,
    onRefresh: () -> Unit
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "No articles available",
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center
            )
            OutlinedButton(onClick = onRefresh) {
                Text("Refresh")
            }
        }
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun HomePreview() {
    val sampleArticles = listOf(
        Post(
            id = "1",
            title = "Itthon Ä‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©s EurÄ‚â€žĂ˘â‚¬ĹˇĂ„Ä…Ă˘â‚¬ĹˇpÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡ban is duplÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡zna a kÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â­nai Ä‚â€žĂ˘â‚¬ĹˇĂ„Ä…Ă˘â‚¬ĹˇriÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡s, amely MagyarorszÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡gon mÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡r elÄ‚â€žĂ„â€¦Ä‚ËĂ˘â€šÂ¬Ă‚Âzi a TeslÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡t",
            description = "This is really important",
            imageUrl = "asd",
            category = "KÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€žĂ‹ĹĄlfÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â¶ld",
            source = "24.hu"
        ),
        Post(
            id = "2",
            title = "BÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©rfizetÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©si problÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©ma: egy hÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©vÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â­zi hÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡romcsillagos szÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡lloda dolgozÄ‚â€žĂ˘â‚¬ĹˇĂ„Ä…Ă˘â‚¬Ĺˇi nem kaptÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡k meg fizetÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©sÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€žĂ‹ĹĄket",
            description = "This is really important",
            imageUrl = "asd",
            category = "BelfÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â¶ld",
            source = "Telex"
        ),
        Post(
            id = "3",
            title = "ElÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡rulta az ETO edzÄ‚â€žĂ„â€¦Ä‚ËĂ˘â€šÂ¬Ă‚Âje, hol folytatja a pÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡lyafutÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡sÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€ąĂ˘â‚¬Ë‡t",
            description = "This is really important",
            imageUrl = "asd",
            category = "Foci",
            source = "24.hu"
        ),
        Post(
            id = "4",
            title = "\"Biztos, hogy nem\" Ă„â€šĂ‹ÂÄ‚ËĂ˘â‚¬ĹˇĂ‚Â¬Ä‚ËĂ˘â€šÂ¬Äąâ€ş Havasi Bertalan karrierjÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©nek emlÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©kÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â©re",
            description = "This is really important",
            imageUrl = "asd",
            category = "BelfÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â¶ld",
            source = "24.hu"
        )
    )

    val pagingDataFlow = flowOf(PagingData.from(sampleArticles))
    val lazyPagingItems = pagingDataFlow.collectAsLazyPagingItems()

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
                HomeScreen(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .padding(top = 12.dp),
                    articles = lazyPagingItems,
                    onNavigationEvent = {}
                )
            }
        }
    }
}
