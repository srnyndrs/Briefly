package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.BellSlash
import com.composables.icons.heroicons.outline.Link
import com.composables.icons.heroicons.outline.Plus
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.components.ArticleCard
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun FeedDetailsScreen(
    modifier: Modifier = Modifier,
    feedDetailsState: UiState<FeedSourceDetails>,
) {
    Column(
        modifier = Modifier.then(modifier)
            .padding(horizontal = 6.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Source card
        Row(
            modifier = Modifier.fillMaxWidth()
                .padding(top = 12.dp)
                .border(
                    1.dp,
                    MaterialTheme.colorScheme.onSurface,
                    RoundedCornerShape(5.dp)
                ),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            when(feedDetailsState) {
                is UiState.Success -> {
                    val feedDetails = feedDetailsState.data

                    RemoteImageContainer(
                        modifier = Modifier.size(126.dp),
                        imageUrl = feedDetails.imageUrl ?: ""
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
                            text = feedDetails.title ?: "",
                            style = MaterialTheme.typography.titleLarge,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        // Source description
                        Text(
                            text = feedDetails.description ?: "",
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 3,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
                else -> {
                    LinearProgressIndicator()
                }
            }
        }
        // Actions
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            OutlinedIconButton(
                onClick = {

                }
            ) {
                Icon(
                    imageVector = Heroicons.Outline.BellSlash,
                    contentDescription = null
                )
            }
            OutlinedButton(
                modifier = Modifier.wrapContentWidth(),
                shape = RoundedCornerShape(5.dp),
                onClick = {

                }
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Icon(
                        modifier = Modifier.size(16.dp),
                        imageVector = Heroicons.Outline.Plus,
                        contentDescription = "Follow feed" // TODO
                    )
                    Text(
                        text = "Follow"
                    )
                }
            }
            OutlinedButton(
                modifier = Modifier.wrapContentWidth(),
                shape = RoundedCornerShape(5.dp),
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
            items(5) {
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
                feedDetailsState = UiState.Success(
                    data = FeedSourceDetails(
                        id = "1",
                        title = "24.hu",
                        description = "Hírek, podcastek stb."
                    )
                )
            )
        }
    }
}
