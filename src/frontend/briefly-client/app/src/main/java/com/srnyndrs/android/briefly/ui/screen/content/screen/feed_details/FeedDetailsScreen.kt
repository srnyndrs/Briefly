package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedIconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ArrowPath
import com.composables.icons.heroicons.outline.Bell
import com.composables.icons.heroicons.outline.BellSlash
import com.composables.icons.heroicons.outline.Calendar
import com.composables.icons.heroicons.outline.CloudArrowDown
import com.composables.icons.heroicons.outline.Heart
import com.composables.icons.heroicons.outline.Link
import com.composables.icons.heroicons.solid.Heart
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.common.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleCard
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details.preview.FeedDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.math.max
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
@Composable
fun FeedDetailsScreen(
    modifier: Modifier = Modifier,
    state: FeedDetailsState,
    onNavigationEvent: (ContentNavigationEvent) -> Unit
) {

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier.then(modifier)
            .verticalScroll(scrollState)
            .padding(horizontal = 6.dp),
        verticalArrangement = Arrangement.spacedBy(32.dp)
    ) {
        UiStateContainer(
            modifier = Modifier.fillMaxWidth(),
            state = state.feedDetails
        ) { feedDetails, isLoading ->
            Column(
                modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
                verticalArrangement = Arrangement.spacedBy(22.dp)
            ) {
                // New source card
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(22.dp)
                ) {
                    ShimmerItem(
                        modifier = Modifier
                            .fillMaxWidth()
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
                                    .requiredHeight(36.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                // Picture
                                RemoteImageContainer(
                                    modifier = Modifier.size(36.dp),
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
                            OutlinedButton(
                                modifier = Modifier.wrapContentWidth(),
                                shape = RoundedCornerShape(5.dp),
                                enabled = !isLoading,
                                colors = ButtonDefaults.outlinedButtonColors(
                                    containerColor = Color.Transparent,
                                    disabledContainerColor = Color.Transparent,
                                ),
                                onClick = {
                                    // TODO: extract url
                                    //onNavigationEvent(ContentNavigationEvent.OpenCustomTab(url = ""))
                                }
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    Icon(
                                        modifier = Modifier.size(16.dp),
                                        imageVector = Heroicons.Outline.Link,
                                        contentDescription = "Visit website" // TODO
                                    )
                                    Text(
                                        text = "Visit website"
                                    )
                                }
                            }
                        }
                    }
                    // Description
                    if(isLoading) {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            repeat(3) {
                                ShimmerItem(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .requiredHeight(12.dp),
                                    isLoading = true,
                                    cornerRadius = 3.dp
                                ) { }
                            }
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
                    // Divider
                    HorizontalDivider(
                        modifier = Modifier.fillMaxWidth(),
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(0.4f)
                    )
                    // Actions
                    ShimmerItem(
                        modifier = Modifier.defaultMinSize(128.dp, 24.dp),
                        isLoading = isLoading,
                        cornerRadius = 3.dp
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp, horizontal = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(
                                modifier = Modifier.weight(0.5f),
                                horizontalArrangement = Arrangement.Start,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(
                                    modifier = Modifier.padding(horizontal = 12.dp),
                                    verticalArrangement = Arrangement.spacedBy(12.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Row(
                                        modifier = Modifier.wrapContentSize(),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(24.dp),
                                            imageVector = Heroicons.Outline.CloudArrowDown,
                                            contentDescription = null
                                        )
                                        Text(
                                            text = "Last updated",
                                            style = MaterialTheme.typography.bodyLarge,
                                        )
                                    }
                                    Text(
                                        text = feedDetails?.lastUpdatedAt?.toRelativeArticleTime() ?: "",
                                        style = MaterialTheme.typography.bodyLarge,
                                        maxLines = 1,
                                    )
                                }
                            }
                            Row(
                                modifier = Modifier.weight(0.5f),
                                horizontalArrangement = Arrangement.End,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                OutlinedIconButton(
                                    modifier = Modifier.size(52.dp),
                                    enabled = !isLoading,
                                    onClick = {

                                    }
                                ) {
                                    Icon(
                                        modifier = Modifier.size(32.dp),
                                        imageVector = if (feedDetails?.subscribed!!) Heroicons.Outline.BellSlash else Heroicons.Outline.Bell,
                                        contentDescription = null
                                    )
                                }
                                Spacer(
                                    modifier = Modifier.requiredWidth(18.dp)
                                )
                                OutlinedIconButton(
                                    modifier = Modifier.size(52.dp),
                                    enabled = !isLoading,
                                    onClick = {

                                    }
                                ) {
                                    Icon(
                                        modifier = Modifier.size(32.dp),
                                        imageVector = if (feedDetails?.favourite!!) Heroicons.Solid.Heart else Heroicons.Outline.Bell,
                                        contentDescription = null
                                    )
                                }
                            }
                        }
                    }
                }
                // Actions
                /*
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(42.dp),
                    isLoading = isLoading,
                    cornerRadius = 5.dp
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        OutlinedIconButton(
                            modifier = Modifier.size(42.dp),
                            enabled = !isLoading,
                            onClick = {

                            }
                        ) {
                            Icon(
                                imageVector = if (feedDetails?.subscribed!!) Heroicons.Outline.BellSlash else Heroicons.Outline.Bell,
                                contentDescription = null
                            )
                        }
                        OutlinedButton(
                            modifier = Modifier.wrapContentWidth(),
                            shape = RoundedCornerShape(5.dp),
                            enabled = !isLoading,
                            onClick = {

                            }
                        ) {
                            val followed = feedDetails?.favourite ?: false
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    modifier = Modifier.size(16.dp),
                                    imageVector = if(!followed) Heroicons.Solid.Heart else Heroicons.Outline.Heart,
                                    contentDescription = if(!followed) "Follow" else "Unfollow"
                                )
                                Text(
                                    text = if(!followed) "Follow" else "Unfollow"
                                )
                            }
                        }
                        OutlinedButton(
                            modifier = Modifier.wrapContentWidth(),
                            shape = RoundedCornerShape(5.dp),
                            enabled = !isLoading,
                            onClick = {

                            }
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    modifier = Modifier.size(16.dp),
                                    imageVector = Heroicons.Outline.Link,
                                    contentDescription = "Visit website" // TODO
                                )
                                Text(
                                    text = "Visit website"
                                )
                            }
                        }
                    }
                }*/
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
                if(isLoading) {
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
                    for(article in articles ?: emptyList()) {
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
                state = state
            ) {}
        }
    }
}
