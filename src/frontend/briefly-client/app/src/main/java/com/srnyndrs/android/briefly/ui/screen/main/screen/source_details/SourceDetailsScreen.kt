package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonColors
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedIconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
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
import com.srnyndrs.android.briefly.ui.components.OutlinedVerifiedBadge
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.main.components.PostItemCard
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.preview.SourceDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
@Composable
fun SourceDetailsScreen(
    modifier: Modifier = Modifier,
    state: SourceDetailsState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onEvent: (SourceDetailsEvent) -> Unit
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
                                .defaultMinSize(minHeight = 56.dp),
                            isLoading = isLoading,
                            cornerRadius = 5.dp
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(
                                    modifier = Modifier.weight(0.7f)
                                        .requiredHeight(42.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    // Picture
                                    RemoteImageContainer(
                                        modifier = Modifier.size(42.dp),
                                        imageUrl = feedDetails?.imageUrl ?: "",
                                        contentScale = ContentScale.Fit
                                    )
                                    Spacer(modifier = Modifier.requiredWidth(4.dp))
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
                                    // Verified badge
                                    if(feedDetails?.verified == true) {
                                        /*Icon(
                                            modifier = Modifier.size(28.dp),
                                            imageVector = Heroicons.Outline.CheckBadge,
                                            tint = MaterialTheme.colorScheme.primary,
                                            contentDescription = null
                                        )*/
                                        OutlinedVerifiedBadge(
                                            modifier = Modifier.size(20.dp),
                                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(0.7f),
                                            innerPadding = 4.dp,
                                            wavesCount = 8,
                                            waveAmplitude = 3f
                                        )
                                    }
                                }
                                Row(
                                    modifier = Modifier.weight(0.3f),
                                    horizontalArrangement = Arrangement.End,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    OutlinedIconButton(
                                        modifier = Modifier.size(42.dp),
                                        enabled = !isLoading,
                                        onClick = {
                                            feedDetails?.followed?.let {
                                                onEvent(SourceDetailsEvent.ToggleFollow(it))
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
                                                onEvent(SourceDetailsEvent.ToggleSubscribe(it))
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
                                TextButton(
                                    shape = RoundedCornerShape(8.dp),
                                    enabled = !isLoading,
                                    colors = ButtonDefaults.outlinedButtonColors(
                                        containerColor = Color.Transparent,
                                        disabledContainerColor = Color.Transparent,
                                        contentColor = MaterialTheme.colorScheme.onSurface,
                                        disabledContentColor = MaterialTheme.colorScheme.onSurface,
                                    ),
                                    border = BorderStroke(
                                        width = 1.dp,
                                        color = MaterialTheme.colorScheme.onSurface.copy(0.2f)
                                    ),
                                    onClick = {},
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(22.dp),
                                            imageVector = Heroicons.Outline.CloudArrowDown,
                                            contentDescription = null,
                                        )
                                        Text(
                                            text = feedDetails?.lastUpdatedAt?.toRelativeArticleTime()
                                                ?: "",
                                            style = MaterialTheme.typography.bodyMedium,
                                            maxLines = 1,
                                        )
                                    }
                                }
                                TextButton(
                                    shape = RoundedCornerShape(8.dp),
                                    enabled = !isLoading && feedDetails?.websiteUrl != null,
                                    colors = ButtonDefaults.outlinedButtonColors(
                                        containerColor = Color.Transparent,
                                        disabledContainerColor = Color.Transparent,
                                        contentColor = MaterialTheme.colorScheme.onSurface,
                                        disabledContentColor = MaterialTheme.colorScheme.onSurface,
                                    ),
                                    border = BorderStroke(
                                        width = 1.dp,
                                        color = MaterialTheme.colorScheme.onSurface.copy(0.2f)
                                    ),
                                    onClick = {
                                        onNavigationEvent(
                                            MainNavigationEvent.OpenCustomTab(
                                                url = feedDetails?.websiteUrl
                                            )
                                        )
                                    },
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(22.dp),
                                            imageVector = Heroicons.Outline.ArrowTopRightOnSquare,
                                            contentDescription = null,
                                        )
                                        Text(
                                            text = "Visit website",
                                            style = MaterialTheme.typography.bodyMedium,
                                            maxLines = 1,
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
                        text = "Latest articles", // TODO: stringResource
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
                            PostItemCard(
                                modifier = Modifier
                                    .fillMaxHeight()
                                    .requiredHeight(128.dp),
                                title = "Title",
                                category = "Category",
                                imageUrl = "",
                                description = "",
                                isLoading = true
                            )
                        }
                    } else {
                        for (article in articles ?: emptyList()) {
                            /*PostCard(
                                title = article.title,
                                description = article.description ?: "",
                                imageUrl = article.imageUrl
                            ) {
                                onNavigationEvent(MainNavigationEvent.ShowPostDetails(article.id))
                            }*/
                            PostItemCard(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(128.dp),
                                title = article.title,
                                category = article.category ?: "", // TODO
                                imageUrl = article.imageUrl,
                                publishDate = article.publishDate,
                                description = article.description ?: "",
                                isLoading = false,
                            ) {
                                if (article.hasContent) {
                                    onNavigationEvent(MainNavigationEvent.ShowPostDetails(article.id))
                                } else {
                                    onNavigationEvent(MainNavigationEvent.OpenCustomTab(article.url))
                                }
                            }
                            /*HorizontalDivider(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp),
                                thickness = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface.copy(0.4f)
                            )*/
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
            Row(
                modifier = Modifier.weight(0.7f),
                horizontalArrangement = Arrangement.spacedBy(18.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Back button
                IconButton(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(CircleShape),
                    onClick = { onNavigationEvent(MainNavigationEvent.NavigateBack) },
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
            IconButton(
                onClick = {
                    // TODO
                }
            ) {
                Column(
                    verticalArrangement = Arrangement.spacedBy(3.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    repeat(3) {
                        Box(
                            modifier = Modifier
                                .size(4.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.onSurface)
                        )
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun SourceDetailsScreenPreview(
    @PreviewParameter(SourceDetailsStateProvider::class) state: SourceDetailsState
) {
    BrieflyTheme {
        Surface {
            SourceDetailsScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onNavigationEvent = {}
            ) {}
        }
    }
}
