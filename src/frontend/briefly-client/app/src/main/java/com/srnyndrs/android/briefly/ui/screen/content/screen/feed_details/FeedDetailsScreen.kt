package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonColors
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedIconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ArrowTopRightOnSquare
import com.composables.icons.heroicons.outline.Bell
import com.composables.icons.heroicons.outline.BellSlash
import com.composables.icons.heroicons.outline.ChevronLeft
import com.composables.icons.heroicons.outline.CloudArrowDown
import com.composables.icons.heroicons.outline.Heart
import com.composables.icons.heroicons.solid.Heart
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.common.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleCard
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details.preview.FeedDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
@Composable
fun FeedDetailsScreen(
    modifier: Modifier = Modifier,
    state: FeedDetailsState,
    onNavigationEvent: (ContentNavigationEvent) -> Unit,
    onEvent: (FeedDetailsEvent) -> Unit
) {

    val scrollState = rememberScrollState()

    Box(
        modifier = Modifier.then(modifier)
            .padding(horizontal = 12.dp)
            .verticalScroll(scrollState)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(top = 70.dp),
            verticalArrangement = Arrangement.spacedBy(32.dp)
        ) {
            UiStateContainer(
                modifier = Modifier.fillMaxWidth(),
                state = state.feedDetails
            ) { feedDetails, isLoading ->
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 12.dp),
                    verticalArrangement = Arrangement.spacedBy(22.dp)
                ) {
                    // New source card
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(18.dp)
                    ) {
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp)
                                .defaultMinSize(minHeight = 36.dp),
                            isLoading = isLoading,
                            cornerRadius = 5.dp
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(
                                    modifier = Modifier.weight(0.5f)
                                        .requiredHeight(42.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    // Picture
                                    RemoteImageContainer(
                                        modifier = Modifier.size(42.dp),
                                        imageUrl = feedDetails?.imageUrl ?: "",
                                        contentScale = ContentScale.Fit
                                    )
                                    // Title
                                    Text(
                                        modifier = Modifier.padding(horizontal = 8.dp),
                                        text = feedDetails?.title ?: "",
                                        style = MaterialTheme.typography.bodyLarge,
                                        fontSize = 24.sp,
                                        textAlign = TextAlign.Start,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                                Row(
                                    modifier = Modifier.weight(0.5f),
                                    horizontalArrangement = Arrangement.End,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    OutlinedIconButton(
                                        modifier = Modifier.size(42.dp),
                                        enabled = !isLoading,
                                        onClick = {
                                            feedDetails?.followed?.let {
                                                onEvent(FeedDetailsEvent.ToggleFollow(it))
                                            }
                                        }
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(32.dp),
                                            imageVector = if (feedDetails?.followed!!) Heroicons.Outline.BellSlash else Heroicons.Outline.Bell,
                                            contentDescription = null
                                        )
                                    }
                                    Spacer(
                                        modifier = Modifier.requiredWidth(16.dp)
                                    )
                                    OutlinedIconButton(
                                        modifier = Modifier.size(42.dp),
                                        enabled = !isLoading,
                                        onClick = {
                                            feedDetails?.subscribed?.let {
                                                onEvent(FeedDetailsEvent.ToggleSubscribe(it))
                                            }
                                        }
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(32.dp),
                                            imageVector = if (feedDetails?.subscribed!!) Heroicons.Solid.Heart else Heroicons.Outline.Heart,
                                            contentDescription = null
                                        )
                                    }
                                }
                            }
                        }
                        // Description
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Text(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(bottom = 8.dp),
                                text = "Description",
                                style = MaterialTheme.typography.labelLarge,
                                fontWeight = FontWeight.Black
                            )
                            if (isLoading) {
                                repeat(3) {
                                    ShimmerItem(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .requiredHeight(12.dp),
                                        isLoading = true,
                                        cornerRadius = 3.dp
                                    ) { }
                                }
                            } else {
                                Text(
                                    modifier = Modifier.fillMaxWidth(),
                                    text = feedDetails?.description ?: "",
                                    style = MaterialTheme.typography.bodyLarge.copy(
                                        letterSpacing = TextUnit.Unspecified
                                    ),
                                    textAlign = TextAlign.Justify,
                                )
                            }
                        }
                        // Actions
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .defaultMinSize(minHeight = 32.dp),
                            isLoading = isLoading,
                            cornerRadius = 3.dp
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(top = 12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(
                                    modifier = Modifier.wrapContentWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        modifier = Modifier.size(28.dp),
                                        imageVector = Heroicons.Outline.CloudArrowDown,
                                        contentDescription = null
                                    )
                                    Text(
                                        text = feedDetails?.lastUpdatedAt?.toRelativeArticleTime()
                                            ?: "",
                                        style = MaterialTheme.typography.bodyMedium,
                                        maxLines = 1,
                                    )
                                }
                                Row(
                                    modifier = Modifier.wrapContentWidth()
                                        .clickable(
                                            enabled = !isLoading && feedDetails?.websiteUrl != null
                                        ) {
                                            onNavigationEvent(
                                                ContentNavigationEvent.OpenCustomTab(
                                                    url = feedDetails?.websiteUrl
                                                )
                                            )
                                        },
                                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "Visit website",
                                        style = MaterialTheme.typography.bodyMedium,
                                        maxLines = 1,
                                    )
                                    Box(
                                        modifier = Modifier.size(28.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(22.dp),
                                            imageVector = Heroicons.Outline.ArrowTopRightOnSquare,
                                            contentDescription = null
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
            UiStateContainer(
                modifier = Modifier.fillMaxWidth(),
                state = state.articles
            ) { articles, isLoading ->
                // Latest articles
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Latest articles",
                        style = MaterialTheme.typography.titleLarge,
                    )
                    HorizontalDivider(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 6.dp),
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    if (isLoading) {
                        repeat(3) {
                            ArticleCard(
                                modifier = Modifier
                                    .fillMaxHeight()
                                    .requiredHeight(72.dp),
                                title = "Title",
                                description = "Description",
                                imageUrl = "",
                                isLoading = isLoading
                            )
                        }
                    } else {
                        for (article in articles ?: emptyList()) {
                            ArticleCard(
                                title = article.title,
                                description = article.description ?: "",
                                imageUrl = article.imageUrl
                            ) {
                                onNavigationEvent(ContentNavigationEvent.ShowArticleDetails(article.id))
                            }
                            HorizontalDivider(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp),
                                thickness = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface.copy(0.4f)
                            )
                        }
                    }
                }
            }
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp)
                .align(Alignment.TopStart),
            horizontalArrangement = Arrangement.spacedBy(18.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Back button
            IconButton(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape),
                onClick = { onNavigationEvent(ContentNavigationEvent.NavigateBack) },
                colors = IconButtonColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(0.7f),
                    contentColor = MaterialTheme.colorScheme.onSurface,
                    disabledContainerColor = MaterialTheme.colorScheme.surface,
                    disabledContentColor = MaterialTheme.colorScheme.onSurface
                )
            ) {
                Icon(
                    modifier = Modifier.size(28.dp),
                    imageVector = Heroicons.Outline.ChevronLeft,
                    contentDescription = null
                )
            }
            // Title
            Text(
                text = "Feed Details",
                style = MaterialTheme.typography.headlineSmall
            )
        }
    }
}

@PreviewLightDark
@Composable
fun FeedDetailsScreenPreview(
    @PreviewParameter(FeedDetailsStateProvider::class) state: FeedDetailsState
) {
    BrieflyTheme {
        Surface {
            FeedDetailsScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onNavigationEvent = {}
            ) {}
        }
    }
}
