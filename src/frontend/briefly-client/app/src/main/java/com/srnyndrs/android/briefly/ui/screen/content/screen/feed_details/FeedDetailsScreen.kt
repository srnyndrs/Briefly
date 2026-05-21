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
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedIconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Bell
import com.composables.icons.heroicons.outline.BellSlash
import com.composables.icons.heroicons.outline.Link
import com.composables.icons.heroicons.outline.Minus
import com.composables.icons.heroicons.outline.Plus
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.common.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleCard
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.shimmer

@Composable
fun FeedDetailsScreen(
    modifier: Modifier = Modifier,
    state: FeedDetailsState,
) {
    Column(
        modifier = Modifier.then(modifier).padding(horizontal = 6.dp),
        verticalArrangement = Arrangement.spacedBy(22.dp)
    ) {
        UiStateContainer(
            modifier = Modifier.fillMaxWidth(),
            state = state.feedDetails
        ) { feedDetails, isLoading ->
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(22.dp)
            ) {
                // Source card
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(196.dp)
                        .padding(top = 12.dp)
                        .border(
                            1.dp,
                            MaterialTheme.colorScheme.onSurface,
                            RoundedCornerShape(5.dp)
                        ),
                    isLoading = isLoading
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        RemoteImageContainer(
                            modifier = Modifier.size(126.dp),
                            imageUrl = feedDetails?.imageUrl ?: ""
                        )
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(6.dp),
                            horizontalAlignment = Alignment.Start,
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            // Source title
                            Text(
                                text = feedDetails?.title ?: "",
                                style = MaterialTheme.typography.titleLarge,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            // Source description
                            Text(
                                text = feedDetails?.description ?: "",
                                style = MaterialTheme.typography.bodyMedium,
                                maxLines = 3,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
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
                                modifier = Modifier.fillMaxSize(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    modifier = Modifier.size(16.dp),
                                    imageVector = if(!followed) Heroicons.Outline.Plus else Heroicons.Outline.Minus,
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
                                modifier = Modifier.fillMaxSize(),
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
                if(articles?.isNotEmpty() == true) {
                    items(articles) {
                        ArticleCard(
                            title = "Breaking news!",
                            source = null,
                            description = "Something happened",
                            imageUrl = ""
                        ) {

                        }
                        HorizontalDivider(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                } else {
                    items(3) {
                        LinearProgressIndicator()
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun FeedDetailsScreenPreview() {
    BrieflyTheme {
        Surface {
            FeedDetailsScreen(
                modifier = Modifier.fillMaxSize(),
                state = FeedDetailsState(
                    feedDetails = /*UiState.Success(
                        FeedSourceDetails(
                            id = "1",
                            title = "24.hu",
                            description = "Hírek, podcastek stb.",
                            favourite = true
                        )
                    )*/
                    UiState.Loading
                    ,
                    articles = UiState.Success(
                        listOf(
                            ArticleItem(
                                id = "1",
                                title = "Breaking news!",
                            )
                        )
                    )
                )
            )
        }
    }
}
