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
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
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
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleRow
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentNavigationEvent
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.flowOf

@Composable
fun ContentExploreScreen(
    modifier: Modifier = Modifier,
    articles: LazyPagingItems<ArticleItem>,
    onNavigationEvent: (ContentNavigationEvent) -> Unit,
) {
    var selectedCategoryIndex by rememberSaveable {
        mutableIntStateOf(0)
    }

    when (val refreshState = articles.loadState.refresh) {
        is LoadState.Loading -> {
            ContentExploreLoadingSkeleton(
                modifier = modifier.padding(horizontal = 8.dp),
                selectedCategoryIndex = selectedCategoryIndex
            )
        }
        is LoadState.Error -> {
            ContentExploreErrorState(
                modifier = modifier.fillMaxSize().padding(16.dp),
                errorMessage = refreshState.error.localizedMessage ?: "Failed to load articles",
                onRetry = { articles.retry() }
            )
        }
        is LoadState.NotLoading -> {
            if (articles.itemCount == 0) {
                ContentExploreEmptyState(
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
                                            ContentNavigationEvent.ShowArticleDetails(article.id)
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

                    // 3. Category selectors
                    item(key = "categories") {
                        CategorySelectorRow(
                            selectedIndex = selectedCategoryIndex,
                            onCategorySelected = { selectedCategoryIndex = it }
                        )
                    }

                    // 4. Paginated article items
                    val remainingCount = (articles.itemCount - numberOfHeadliners).coerceAtLeast(0)
                    items(
                        count = remainingCount,
                        key = { index -> articles.peek(index + numberOfHeadliners)?.id ?: "article_$index" }
                    ) { index ->
                        val article = articles[index + numberOfHeadliners]
                        if (article != null) {
                            ArticleRow(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp),
                                title = article.title,
                                source = article.source
                            ) {
                                if (article.hasContent) {
                                    onNavigationEvent(
                                        ContentNavigationEvent.ShowArticleDetails(article.id)
                                    )
                                } else {
                                    onNavigationEvent(
                                        ContentNavigationEvent.OpenCustomTab(article.url)
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
    article: ArticleItem,
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
private fun CategorySelectorRow(
    modifier: Modifier = Modifier,
    selectedIndex: Int,
    isLoading: Boolean = false,
    onCategorySelected: (Int) -> Unit = {}
) {
    val options = listOf(
        "Összes",
        "Sport",
        "Belföld",
        "Külföld",
        "Kultúra"
    )
    LazyRow(
        modifier = modifier
            .fillMaxWidth()
            .padding(bottom = 18.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        items(options.size) { index ->
            val selected = index == selectedIndex
            ShimmerItem(
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
                            onCategorySelected(index)
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
}

@Composable
private fun ContentExploreLoadingSkeleton(
    modifier: Modifier = Modifier,
    selectedCategoryIndex: Int
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

        // Category skeleton
        CategorySelectorRow(
            selectedIndex = selectedCategoryIndex,
            isLoading = true
        )

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
private fun ContentExploreErrorState(
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
private fun ContentExploreEmptyState(
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

@PreviewLightDark
@Composable
fun ContentExplorePreview() {
    val sampleArticles = listOf(
        ArticleItem(
            id = "1",
            title = "Itthon és Európában is duplázna a kínai óriás, amely Magyarországon már előzi a Teslát",
            description = "This is really important",
            imageUrl = "asd",
            category = "Külföld",
            source = "24.hu"
        ),
        ArticleItem(
            id = "2",
            title = "Bérfizetési probléma: egy hévízi háromcsillagos szálloda dolgozói nem kapták meg fizetésüket",
            description = "This is really important",
            imageUrl = "asd",
            category = "Belföld",
            source = "Telex"
        ),
        ArticleItem(
            id = "3",
            title = "Elárulta az ETO edzője, hol folytatja a pályafutását",
            description = "This is really important",
            imageUrl = "asd",
            category = "Foci",
            source = "24.hu"
        ),
        ArticleItem(
            id = "4",
            title = "\"Biztos, hogy nem\" – Havasi Bertalan karrierjének emlékére",
            description = "This is really important",
            imageUrl = "asd",
            category = "Belföld",
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
                ContentExploreScreen(
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
