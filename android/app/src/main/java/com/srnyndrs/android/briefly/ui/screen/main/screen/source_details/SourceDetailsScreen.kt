package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
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
import com.composables.icons.heroicons.outline.EllipsisVertical
import com.composables.icons.heroicons.outline.Heart
import com.composables.icons.heroicons.solid.Heart
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.OutlinedVerifiedBadge
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.components.PostItemCard
import com.srnyndrs.android.briefly.ui.screen.main.components.PostItemCardPlaceholder
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
    onEvent: (SourceDetailsEvent) -> Unit,
) {

    val scrollState = rememberScrollState()
    var isSourceMenuExpanded by rememberSaveable { mutableStateOf(false) }
    val subscriptionSavingLabel = stringResource(id = R.string.source_details_subscription_saving)

    Box(
        modifier = Modifier
            .then(modifier)
            .padding(horizontal = 12.dp)
            .verticalScroll(state = scrollState)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(top = 70.dp),
            verticalArrangement = Arrangement.spacedBy(space = 32.dp),
        ) {
            UiStateContainer(
                modifier = Modifier.fillMaxWidth(),
                state = state.feedDetails,
                loading = {
                    ShimmerGroup {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                        ) {
                            repeat(times = 5) { index ->
                                ShimmerItem(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .requiredHeight(height = if (index == 0) 56.dp else 16.dp),
                                    isLoading = true,
                                    cornerRadius = 5.dp,
                                ) {}
                            }
                        }
                    }
                },
                error = {
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                    ) {
                        Text(
                            text = stringResource(id = R.string.source_details_load_error),
                            color = MaterialTheme.colorScheme.error,
                        )
                        Button(onClick = { onEvent(SourceDetailsEvent.RetryFeedDetails) }) {
                            Text(text = stringResource(id = R.string.session_retry))
                        }
                    }
                },
                success = { feedDetails ->
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 12.dp),
                        verticalArrangement = Arrangement.spacedBy(space = 22.dp),
                    ) {
                        // New source card
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(space = 18.dp),
                        ) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 12.dp)
                                    .defaultMinSize(minHeight = 56.dp),
                            ) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .weight(weight = 0.7f)
                                            .requiredHeight(height = 42.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                    ) {
                                        // Picture
                                        RemoteImageContainer(
                                            modifier = Modifier.size(size = 42.dp),
                                            imageUrl = feedDetails.faviconUrl.orEmpty(),
                                            contentDescription = null,
                                            contentScale = ContentScale.Fit,
                                        )
                                        Spacer(modifier = Modifier.requiredWidth(width = 4.dp))
                                        // Title
                                        Text(
                                            modifier = Modifier
                                                .weight(weight = 1f)
                                                .padding(horizontal = 8.dp),
                                            text = feedDetails.title.orEmpty(),
                                            style = MaterialTheme.typography.bodyLarge,
                                            fontSize = 24.sp,
                                            textAlign = TextAlign.Start,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                        )
                                        // Verified badge
                                        if (feedDetails.verified) {
                                            OutlinedVerifiedBadge(
                                                modifier = Modifier.size(size = 20.dp),
                                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
                                                innerPadding = 4.dp,
                                                wavesCount = 8,
                                                waveAmplitude = 3f,
                                            )
                                        }
                                    }
                                    Row(
                                        modifier = Modifier.weight(weight = 0.3f),
                                        horizontalArrangement = Arrangement.End,
                                        verticalAlignment = Alignment.CenterVertically,
                                    ) {
                                        OutlinedIconButton(
                                            modifier = Modifier.size(size = 42.dp),
                                            enabled = !state.isUpdatingSubscription,
                                            onClick = {
                                                onEvent(SourceDetailsEvent.ToggleSubscribe)
                                            },
                                        ) {
                                            if (state.isUpdatingSubscription) {
                                                CircularProgressIndicator(
                                                    modifier = Modifier
                                                        .size(size = 24.dp)
                                                        .semantics { contentDescription = subscriptionSavingLabel },
                                                    strokeWidth = 2.dp,
                                                )
                                            } else {
                                                Icon(
                                                    modifier = Modifier.size(size = 32.dp),
                                                    imageVector = if (feedDetails.isSubscribed) {
                                                        Heroicons.Solid.Heart
                                                    } else {
                                                        Heroicons.Outline.Heart
                                                    },
                                                    contentDescription = stringResource(
                                                        id = if (feedDetails.isSubscribed) R.string.source_details_unsubscribe
                                                        else R.string.source_details_subscribe,
                                                    ),
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                            if (state.subscriptionUpdateFailed) {
                                Column(verticalArrangement = Arrangement.spacedBy(space = 8.dp)) {
                                    Text(
                                        text = stringResource(id = R.string.source_details_subscription_failed),
                                        color = MaterialTheme.colorScheme.error,
                                    )
                                    Button(onClick = { onEvent(SourceDetailsEvent.ToggleSubscribe) }) {
                                        Text(text = stringResource(id = R.string.session_retry))
                                    }
                                }
                            }
                            // Description
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                verticalArrangement = Arrangement.spacedBy(space = 4.dp),
                            ) {
                                Text(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(bottom = 8.dp),
                                    text = stringResource(id = R.string.source_details_description),
                                    style = MaterialTheme.typography.labelLarge,
                                    fontWeight = FontWeight.Black,
                                )
                                Text(
                                    modifier = Modifier.fillMaxWidth(),
                                    text = feedDetails.description ?: "",
                                    style = MaterialTheme.typography.bodyLarge.copy(
                                        letterSpacing = TextUnit.Unspecified,
                                    ),
                                    textAlign = TextAlign.Justify,
                                )
                            }
                            // Actions
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .defaultMinSize(minHeight = 32.dp),
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(top = 12.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                ) {
                                    Surface(
                                        modifier = Modifier.padding(vertical = 8.dp),
                                        shape = RoundedCornerShape(size = 8.dp),
                                        color = Color.Transparent,
                                        border = BorderStroke(
                                            width = 1.dp,
                                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f),
                                        ),
                                    ) {
                                        Row(
                                            modifier = Modifier.padding(
                                                horizontal = 12.dp,
                                                vertical = 8.dp,
                                            ),
                                            verticalAlignment = Alignment.CenterVertically,
                                            horizontalArrangement = Arrangement.spacedBy(space = 6.dp),
                                        ) {
                                            Icon(
                                                modifier = Modifier.size(size = 22.dp),
                                                imageVector = Heroicons.Outline.CloudArrowDown,
                                                contentDescription = null,
                                            )
                                            Text(
                                                text = feedDetails.lastUpdatedAt.toRelativeArticleTime(),
                                                style = MaterialTheme.typography.bodyMedium,
                                                maxLines = 1,
                                            )
                                        }
                                    }
                                    TextButton(
                                        shape = RoundedCornerShape(size = 8.dp),
                                        enabled = feedDetails.siteUrl != null,
                                        colors = ButtonDefaults.outlinedButtonColors(
                                            containerColor = Color.Transparent,
                                            disabledContainerColor = Color.Transparent,
                                            contentColor = MaterialTheme.colorScheme.onSurface,
                                            disabledContentColor = MaterialTheme.colorScheme.onSurface,
                                        ),
                                        border = BorderStroke(
                                            width = 1.dp,
                                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f),
                                        ),
                                        onClick = {
                                            onNavigationEvent(
                                                MainNavigationEvent.OpenCustomTab(
                                                    url = feedDetails.siteUrl,
                                                )
                                            )
                                        },
                                    ) {
                                        Row(
                                            verticalAlignment = Alignment.CenterVertically,
                                            horizontalArrangement = Arrangement.spacedBy(space = 6.dp),
                                        ) {
                                            Icon(
                                                modifier = Modifier.size(size = 22.dp),
                                                imageVector = Heroicons.Outline.ArrowTopRightOnSquare,
                                                contentDescription = null,
                                            )
                                            Text(
                                                text = stringResource(id = R.string.source_details_visit_website),
                                                style = MaterialTheme.typography.bodyMedium,
                                                maxLines = 1,
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
            )
            UiStateContainer(
                modifier = Modifier.fillMaxWidth(),
                state = state.articles,
                loading = {
                    ShimmerGroup {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                        ) {
                            Text(
                                text = stringResource(id = R.string.source_details_latest_articles),
                                style = MaterialTheme.typography.titleLarge,
                            )
                            HorizontalDivider(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 6.dp),
                                thickness = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                            repeat(times = 3) {
                                PostItemCardPlaceholder(
                                    modifier = Modifier.fillMaxWidth(),
                                )
                            }
                        }
                    }
                },
                error = {
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                    ) {
                        Text(
                            text = stringResource(id = R.string.source_details_articles_error),
                            color = MaterialTheme.colorScheme.error,
                        )
                        Button(onClick = { onEvent(SourceDetailsEvent.RetryArticles) }) {
                            Text(text = stringResource(id = R.string.session_retry))
                        }
                    }
                },
                success = { articles ->
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                    ) {
                        Text(
                            text = stringResource(id = R.string.source_details_latest_articles),
                            style = MaterialTheme.typography.titleLarge,
                        )
                        HorizontalDivider(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                        for (article in articles) {
                            PostItemCard(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(height = 128.dp),
                                title = article.title,
                                categories = article.categories,
                                imageUrl = article.imageUrl,
                                publishedAt = article.publishedAt,
                                description = article.description ?: "",
                            ) {
                                if (article.hasContent) {
                                    onNavigationEvent(MainNavigationEvent.ShowPostDetails(postId = article.id))
                                } else {
                                    onNavigationEvent(MainNavigationEvent.OpenCustomTab(url = article.url))
                                }
                            }
                        }
                    }
                },
            )
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp)
                .align(Alignment.TopStart),
            horizontalArrangement = Arrangement.spacedBy(space = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(
                modifier = Modifier
                    .weight(weight = 0.7f),
                horizontalArrangement = Arrangement.spacedBy(space = 18.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // Back button
                IconButton(
                    modifier = Modifier
                        .size(size = 48.dp)
                        .clip(CircleShape),
                    onClick = { onNavigationEvent(MainNavigationEvent.NavigateBack) },
                    colors = IconButtonColors(
                        containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.7f),
                        contentColor = MaterialTheme.colorScheme.onSurface,
                        disabledContainerColor = MaterialTheme.colorScheme.surface,
                        disabledContentColor = MaterialTheme.colorScheme.onSurface,
                    ),
                ) {
                    Icon(
                        modifier = Modifier.size(size = 28.dp),
                        imageVector = Heroicons.Outline.ChevronLeft,
                        contentDescription = stringResource(id = R.string.navigate_back),
                    )
                }
                // Title
                Text(
                    text = stringResource(id = R.string.source_details_title),
                    style = MaterialTheme.typography.headlineSmall,
                )
            }
            Box {
                IconButton(
                    onClick = { isSourceMenuExpanded = true },
                ) {
                    Icon(
                        imageVector = Heroicons.Outline.EllipsisVertical,
                        contentDescription = stringResource(id = R.string.source_details_more_actions),
                    )
                }
                DropdownMenu(
                    expanded = isSourceMenuExpanded,
                    onDismissRequest = { isSourceMenuExpanded = false },
                ) {
                    when (val blockStatus = state.blockStatus) {
                        is UiState.Success -> {
                            DropdownMenuItem(
                                text = {
                                    Text(
                                        text = stringResource(
                                            id = if (state.isUpdatingBlock) R.string.source_details_block_saving
                                            else if (blockStatus.data) R.string.settings_remove_source
                                            else R.string.source_details_block_source,
                                        ),
                                    )
                                },
                                enabled = !state.isUpdatingBlock,
                                onClick = { onEvent(SourceDetailsEvent.ToggleBlock) },
                            )
                            if (state.blockUpdateFailed) {
                                Text(
                                    modifier = Modifier.padding(horizontal = 16.dp),
                                    text = stringResource(id = R.string.source_details_block_failed),
                                    color = MaterialTheme.colorScheme.error,
                                )
                            }
                        }
                        is UiState.Error -> DropdownMenuItem(
                            text = { Text(text = stringResource(id = R.string.source_details_block_retry)) },
                            onClick = { onEvent(SourceDetailsEvent.RetryBlockStatus) },
                        )
                        else -> DropdownMenuItem(
                            text = { Text(text = stringResource(id = R.string.source_details_block_loading)) },
                            enabled = false,
                            onClick = {},
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
    @PreviewParameter(SourceDetailsStateProvider::class) state: SourceDetailsState,
) {
    BrieflyTheme {
        Surface {
            SourceDetailsScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onNavigationEvent = {},
            ) {}
        }
    }
}
