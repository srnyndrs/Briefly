package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Bell
import com.composables.icons.heroicons.outline.BellSlash
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
import kotlin.math.max

@Composable
fun FeedDetailsScreen(
    modifier: Modifier = Modifier,
    state: FeedDetailsState,
    onNavigationEvent: (ContentNavigationEvent) -> Unit
) {
    Column(
        modifier = Modifier.then(modifier).padding(horizontal = 6.dp),
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
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    ShimmerItem(
                        modifier = Modifier
                            .fillMaxWidth()
                            .defaultMinSize(minHeight = 56.dp),
                        isLoading = isLoading,
                        cornerRadius = 5.dp
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Picture
                            RemoteImageContainer(
                                modifier = Modifier.size(42.dp),
                                imageUrl = feedDetails?.imageUrl ?: ""
                            )
                            // Title
                            Text(
                                modifier = Modifier.fillMaxWidth(),
                                text = feedDetails?.title ?: "",
                                style = MaterialTheme.typography.titleLarge,
                                textAlign = TextAlign.Start,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
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
                            style = MaterialTheme.typography.bodyLarge,
                            textAlign = TextAlign.Justify,
                            letterSpacing = TextUnit.Unspecified
                        )
                    }
                }
                HorizontalDivider(
                    modifier = Modifier.fillMaxWidth(),
                    thickness = 1.dp,
                    color = MaterialTheme.colorScheme.onSurface.copy(0.4f)
                )
                // Actions
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
                        horizontalArrangement = Arrangement.spacedBy(18.dp)
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
                }
            }
        }
        UiStateContainer(
            modifier = Modifier.fillMaxWidth(),
            state = state.articles
        ) { articles, isLoading ->
            // Latest articles
            LazyColumn(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
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
                }
                if(isLoading) {
                    items(3) {
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
                    items(articles ?: emptyList()) { article ->
                        ArticleCard(
                            title = article.title,
                            description = article.description ?: "",
                            imageUrl = article.imageUrl
                        ) {
                            // TODO: onClick
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
