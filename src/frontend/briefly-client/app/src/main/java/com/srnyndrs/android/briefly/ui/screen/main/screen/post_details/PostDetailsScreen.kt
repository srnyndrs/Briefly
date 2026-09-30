package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.BottomSheetDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonColors
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ArrowTopRightOnSquare
import com.composables.icons.heroicons.outline.Check
import com.composables.icons.heroicons.outline.ChevronLeft
import com.composables.icons.heroicons.outline.InformationCircle
import com.composables.icons.heroicons.outline.SpeakerXMark
import com.composables.icons.heroicons.outline.Tag
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.components.PostDetailsPlaceholder
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.preview.PostDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.stringResId
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.time.ExperimentalTime

private enum class PostDetailsDialogContent {
    Details,
    Tags,
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTime::class)
@Composable
fun PostDetailsScreen(
    modifier: Modifier = Modifier,
    state: PostDetailsState,
    onNavigationEvent: (MainNavigationEvent) -> Unit,
    onEvent: (PostDetailsEvent) -> Unit,
) {

    UiStateContainer(
        modifier = Modifier.then(modifier),
        state = state.details,
        loading = {
            PostDetailsPlaceholder(
                modifier = Modifier.fillMaxSize(),
                onBack = { onNavigationEvent(MainNavigationEvent.NavigateBack) },
            )
        },
        error = {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(all = 16.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(text = stringResource(id = R.string.post_details_load_error))
                Button(onClick = { onEvent(PostDetailsEvent.RetryLoad) }) {
                    Text(text = stringResource(id = R.string.session_retry))
                }
                TextButton(onClick = { onNavigationEvent(MainNavigationEvent.NavigateBack) }) {
                    Text(text = stringResource(id = R.string.navigate_back))
                }
            }
        },
        success = { article ->
            val scrollState = rememberScrollState()
            var isDialogVisible by rememberSaveable { mutableStateOf(false) }
            var dialogContent by rememberSaveable { mutableStateOf(PostDetailsDialogContent.Tags) }

            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center,
            ) {
                Box(
                    modifier = Modifier
                        .align(alignment = Alignment.TopCenter)
                        .fillMaxSize(),
                    contentAlignment = Alignment.TopCenter,
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .verticalScroll(state = scrollState),
                        contentAlignment = Alignment.TopCenter,
                    ) {
                        // Image
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(height = 356.dp),
                        ) {
                            // Picture
                            RemoteImageContainer(
                                modifier = Modifier.fillMaxWidth(),
                                imageUrl = article.imageUrl.orEmpty(),
                                contentDescription = null,
                                contentScale = ContentScale.Crop,
                            )
                            // Fade layer
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(color = Color.Black.copy(alpha = 0.12f))
                            )
                        }
                        // Sheet
                        Surface(
                            modifier = Modifier
                                .padding(top = 316.dp)
                                .fillMaxSize()
                                .clip(
                                    RoundedCornerShape(
                                        topStart = 24.dp,
                                        topEnd = 24.dp,
                                    )
                                )
                                .background(color = BottomSheetDefaults.ContainerColor),
                            shadowElevation = 24.dp,
                            contentColor = MaterialTheme.colorScheme.onSurface,
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .padding(
                                        top = 22.dp,
                                        start = 12.dp,
                                        end = 12.dp,
                                    ),
                                verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                            ) {
                                if (article.categories.isNotEmpty()) {
                                    Box(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(bottom = 12.dp),
                                    ) {
                                        FlowRow(
                                            modifier = Modifier.fillMaxWidth(),
                                            verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                                            horizontalArrangement = Arrangement.spacedBy(space = 12.dp),
                                        ) {
                                            article.categories.forEach { category ->
                                                Box(
                                                    modifier = Modifier
                                                        .defaultMinSize(
                                                            minHeight = 36.dp,
                                                            minWidth = 56.dp,
                                                        )
                                                        .clip(shape = RoundedCornerShape(size = 8.dp))
                                                        .background(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.112f)),
                                                    contentAlignment = Alignment.Center,
                                                ) {
                                                    Text(
                                                        modifier = Modifier.padding(
                                                            horizontal = 8.dp,
                                                            vertical = 2.dp,
                                                        ),
                                                        text = stringResource(id = category.stringResId),
                                                        style = MaterialTheme.typography.labelMedium,
                                                        color = MaterialTheme.colorScheme.onSurface,
                                                        fontWeight = FontWeight.Black,
                                                    )
                                                }
                                            }
                                        }

                                    }
                                }
                                // Title
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .defaultMinSize(minHeight = 48.dp),
                                ) {
                                    Text(
                                        modifier = Modifier.fillMaxWidth(),
                                        text = article.title,
                                        style = MaterialTheme.typography.titleLarge,
                                        textAlign = TextAlign.Start,
                                        minLines = 1,
                                    )
                                }
                                // Information's
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .defaultMinSize(minHeight = 26.dp),
                                ) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                    ) {
                                        Row(
                                            modifier = Modifier
                                                .wrapContentSize()
                                                .clickable(
                                                    enabled = article.sourceId != null,
                                                ) {
                                                    article.sourceId?.let {
                                                        onNavigationEvent(
                                                            MainNavigationEvent.ShowSourceDetails(
                                                                sourceId = it,
                                                            )
                                                        )
                                                    }
                                                }
                                        ) {
                                            Text(
                                                text = article.sourceTitle ?: "",
                                                style = MaterialTheme.typography.bodyLarge,
                                            )
                                        }
                                        article.publishedAt?.let { publishedAt ->
                                            Box(
                                                modifier = Modifier
                                                    .size(size = 4.dp)
                                                    .clip(shape = CircleShape)
                                                    .background(color = MaterialTheme.colorScheme.onSurface),
                                            )
                                            Text(
                                                text = publishedAt.toRelativeArticleTime(),
                                                style = MaterialTheme.typography.bodyLarge,
                                            )
                                        }
                                    }
                                }
                                HorizontalDivider(
                                    modifier = Modifier.padding(
                                        bottom = 12.dp,
                                        top = 6.dp,
                                    ),
                                    thickness = 1.dp,
                                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                                )
                                // Content
                                Text(
                                    modifier = Modifier.fillMaxWidth(),
                                    text = article.content.orEmpty(),
                                    style = MaterialTheme.typography.bodyLarge.copy(
                                        letterSpacing = TextUnit.Unspecified,
                                    ),
                                    textAlign = TextAlign.Justify,
                                )
                                Spacer(
                                    modifier = Modifier.requiredHeight(height = 72.dp),
                                )
                            }
                        }
                        // Back button
                        IconButton(
                            modifier = Modifier
                                .padding(all = 12.dp)
                                .size(size = 48.dp)
                                .clip(shape = CircleShape)
                                .align(alignment = Alignment.TopStart),
                            onClick = { onNavigationEvent(MainNavigationEvent.NavigateBack) },
                            colors = IconButtonColors(
                                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.7f),
                                contentColor = MaterialTheme.colorScheme.onSurface,
                                disabledContainerColor = MaterialTheme.colorScheme.surface,
                                disabledContentColor = MaterialTheme.colorScheme.onSurface,
                            )
                        ) {
                            Icon(
                                modifier = Modifier.size(size = 28.dp),
                                imageVector = Heroicons.Outline.ChevronLeft,
                                contentDescription = stringResource(id = R.string.navigate_back),
                            )
                        }
                    }
                    // Bottom Bar
                    Column(
                        modifier = Modifier
                            .align(alignment = Alignment.BottomCenter)
                            .fillMaxWidth()
                            .requiredHeight(height = 72.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(height = 3.dp)
                                .background(
                                    brush = Brush.verticalGradient(
                                        colors = listOf(
                                            Color.Transparent,
                                            MaterialTheme.colorScheme.onSurface.copy(alpha = 0.05f),
                                        ),
                                    ),
                                ),
                        )
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(color = MaterialTheme.colorScheme.surface),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                        ) {
                            HorizontalDivider(
                                thickness = 1.dp,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f),
                            )
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(
                                        start = 10.dp,
                                        end = 10.dp,
                                        bottom = 12.dp,
                                    ),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                // Info
                                TextButton(
                                    shape = RoundedCornerShape(size = 8.dp),
                                    enabled = true,
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
                                        dialogContent = PostDetailsDialogContent.Details
                                        isDialogVisible = true
                                    },
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(space = 6.dp),
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(size = 22.dp),
                                            imageVector = Heroicons.Outline.InformationCircle,
                                            contentDescription = null,
                                        )
                                        Text(
                                            text = stringResource(id = R.string.post_details_details),
                                            style = MaterialTheme.typography.bodyMedium,
                                        )
                                    }
                                }
                                // Tags
                                TextButton(
                                    shape = RoundedCornerShape(size = 8.dp),
                                    enabled = true,
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
                                        dialogContent = PostDetailsDialogContent.Tags
                                        isDialogVisible = true
                                    },
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(space = 6.dp),
                                    ) {
                                        Icon(
                                            modifier = Modifier.size(size = 22.dp),
                                            imageVector = Heroicons.Outline.Tag,
                                            contentDescription = null,
                                        )
                                        Text(
                                            text = stringResource(id = R.string.post_details_tags),
                                            style = MaterialTheme.typography.bodyMedium,
                                        )
                                    }
                                }
                                // External
                                TextButton(
                                    shape = RoundedCornerShape(size = 8.dp),
                                    enabled = true,
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
                                        onNavigationEvent(MainNavigationEvent.OpenCustomTab(url = article.url))
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
                                            text = stringResource(id = R.string.post_details_visit_source),
                                            style = MaterialTheme.typography.bodyMedium,
                                        )
                                    }
                                }
                            }
                        }
                    }
                    if (isDialogVisible) {
                        Dialog(
                            onDismissRequest = { isDialogVisible = false },
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth(fraction = 0.95f)
                                    .requiredHeight(height = 356.dp)
                                    .clip(shape = RoundedCornerShape(size = 5.dp))
                                    .background(color = MaterialTheme.colorScheme.surface)
                                    .padding(all = 24.dp),
                                verticalArrangement = Arrangement.spacedBy(space = 18.dp),
                                horizontalAlignment = Alignment.CenterHorizontally,
                            ) {
                                Text(
                                    text = when (dialogContent) {
                                        PostDetailsDialogContent.Details -> stringResource(id = R.string.post_details_details)
                                        PostDetailsDialogContent.Tags -> stringResource(id = R.string.post_details_keywords)
                                    },
                                    style = MaterialTheme.typography.titleLarge,
                                )
                                HorizontalDivider(
                                    modifier = Modifier.fillMaxWidth(),
                                    thickness = 2.dp,
                                    color = MaterialTheme.colorScheme.onSurface,
                                )
                                when (dialogContent) {
                                    PostDetailsDialogContent.Details -> {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically,
                                        ) {
                                            Text(
                                                text = stringResource(id = R.string.post_details_author),
                                                style = MaterialTheme.typography.bodyLarge,
                                            )
                                            Text(
                                                text = article.author.orEmpty(),
                                                style = MaterialTheme.typography.bodyLarge,
                                            )
                                        }
                                    }

                                    PostDetailsDialogContent.Tags -> {
                                        UiStateContainer(
                                            modifier = Modifier.fillMaxWidth(),
                                            state = state.mutedKeywords,
                                            loading = {
                                                Column(verticalArrangement = Arrangement.spacedBy(space = 8.dp)) {
                                                    Text(text = stringResource(id = R.string.post_details_keywords_loading))
                                                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                                                }
                                            },
                                            error = {
                                                Column(verticalArrangement = Arrangement.spacedBy(space = 8.dp)) {
                                                    Text(
                                                        text = stringResource(id = R.string.post_details_keywords_error),
                                                        color = MaterialTheme.colorScheme.error,
                                                    )
                                                    Button(onClick = { onEvent(PostDetailsEvent.RetryKeywordPreferences) }) {
                                                        Text(text = stringResource(id = R.string.session_retry))
                                                    }
                                                }
                                            },
                                            success = {},
                                        )
                                        state.failedKeyword?.let { keyword ->
                                            Column(verticalArrangement = Arrangement.spacedBy(space = 8.dp)) {
                                                Text(
                                                    text = stringResource(
                                                        id = R.string.post_details_keyword_failed,
                                                        keyword,
                                                    ),
                                                    color = MaterialTheme.colorScheme.error,
                                                )
                                                Button(onClick = { onEvent(PostDetailsEvent.RetryMuteKeyword) }) {
                                                    Text(text = stringResource(id = R.string.session_retry))
                                                }
                                            }
                                        }
                                        val mutedKeywords = (state.mutedKeywords as? UiState.Success)?.data.orEmpty()
                                        LazyColumn(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .weight(weight = 1f),
                                        ) {
                                            items(items = article.keywords) { keyword ->
                                                val isMuted = mutedKeywords.any {
                                                    it.equals(
                                                        other = keyword.trim(),
                                                        ignoreCase = true,
                                                    )
                                                }
                                                Row(
                                                    modifier = Modifier.fillMaxWidth(),
                                                    horizontalArrangement = Arrangement.SpaceBetween,
                                                    verticalAlignment = Alignment.CenterVertically,
                                                ) {
                                                    Text(
                                                        modifier = Modifier.weight(weight = 1f),
                                                        text = keyword,
                                                        style = MaterialTheme.typography.labelMedium,
                                                    )
                                                    IconButton(
                                                        modifier = Modifier.size(size = 48.dp),
                                                        enabled = state.mutedKeywords is UiState.Success &&
                                                            state.mutingKeyword == null && !isMuted,
                                                        onClick = { onEvent(PostDetailsEvent.MuteKeyword(keyword = keyword)) },
                                                    ) {
                                                        if (state.mutingKeyword == keyword.trim()) {
                                                            val savingLabel = stringResource(
                                                                id = R.string.post_details_keyword_saving,
                                                                keyword,
                                                            )
                                                            CircularProgressIndicator(
                                                                modifier = Modifier
                                                                    .size(size = 20.dp)
                                                                    .semantics { contentDescription = savingLabel },
                                                                strokeWidth = 2.dp,
                                                            )
                                                        } else {
                                                            Icon(
                                                                modifier = Modifier.size(size = 20.dp),
                                                                imageVector = if (isMuted) Heroicons.Outline.Check else Heroicons.Outline.SpeakerXMark,
                                                                contentDescription = stringResource(
                                                                    id = if (isMuted) R.string.post_details_keyword_muted
                                                                    else R.string.post_details_mute_keyword,
                                                                    keyword,
                                                                ),
                                                            )
                                                        }
                                                    }
                                                }
                                                HorizontalDivider(
                                                    modifier = Modifier
                                                        .fillMaxWidth()
                                                        .padding(vertical = 12.dp),
                                                    thickness = 1.dp,
                                                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.125f),
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
    )
}

@PreviewLightDark
@Composable
fun PostDetailsScreenPreview(
    @PreviewParameter(PostDetailsStateProvider::class) state: PostDetailsState,
) {
    BrieflyTheme {
        Surface {
            PostDetailsScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onNavigationEvent = {},
                onEvent = {},
            )
        }
    }
}
