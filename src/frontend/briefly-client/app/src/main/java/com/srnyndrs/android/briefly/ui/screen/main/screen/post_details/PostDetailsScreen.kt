package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.BottomSheetDefaults
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonColors
import androidx.compose.material3.IconButtonDefaults
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ArrowTopRightOnSquare
import com.composables.icons.heroicons.outline.ChevronLeft
import com.composables.icons.heroicons.outline.InformationCircle
import com.composables.icons.heroicons.outline.MusicalNote
import com.composables.icons.heroicons.outline.SpeakerXMark
import com.composables.icons.heroicons.outline.Tag
import com.composables.icons.heroicons.solid.SpeakerXMark
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.preview.PostDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
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
    isLoading: Boolean = false,
    article: PostDetails?,
    onNavigationEvent: (MainNavigationEvent) -> Unit
) {

    val scrollState = rememberScrollState()
    var isDialogVisible by rememberSaveable { mutableStateOf(false) }
    var dialogContent by rememberSaveable { mutableStateOf(PostDetailsDialogContent.Tags) }

    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxSize(),
            contentAlignment = Alignment.TopCenter
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(scrollState),
                contentAlignment = Alignment.TopCenter
            ) {
                // Image
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(356.dp),
                    isLoading = isLoading
                ) {
                    // Picture
                    RemoteImageContainer(
                        modifier = Modifier.fillMaxWidth(),
                        imageUrl = article?.imageUrl ?: "",
                        contentScale = ContentScale.Crop
                    )
                    // Fade layer
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color.Black.copy(0.12f))
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
                                topEnd = 24.dp
                            )
                        )
                        .background(BottomSheetDefaults.ContainerColor),
                    shadowElevation = 24.dp,
                    contentColor = MaterialTheme.colorScheme.onSurface,
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(top = 22.dp, start = 12.dp, end = 12.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Category
                            ShimmerItem(
                                modifier = Modifier
                                    .defaultMinSize(minHeight = 36.dp, minWidth = 56.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(MaterialTheme.colorScheme.onSurface.copy(0.112f)),
                                isLoading = isLoading,
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                    text = article?.category ?: "",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    fontWeight = FontWeight.Black
                                )
                            }
                        }
                        // Title
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .defaultMinSize(minHeight = 48.dp),
                            isLoading = isLoading,
                            cornerRadius = 3.dp
                        ) {
                            Text(
                                modifier = Modifier.fillMaxWidth(),
                                text = article?.title ?: "",
                                style = MaterialTheme.typography.titleLarge,
                                textAlign = TextAlign.Start,
                                minLines = 1,
                            )
                        }
                        // Information's
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .defaultMinSize(minHeight = 26.dp),
                            isLoading = isLoading,
                            cornerRadius = 3.dp
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(
                                    modifier = Modifier
                                        .wrapContentSize()
                                        .clickable(
                                            enabled = article?.sourceId != null
                                        ) {
                                            article?.sourceId?.let {
                                                onNavigationEvent(
                                                    MainNavigationEvent.ShowSourceDetails(
                                                        it
                                                    )
                                                )
                                            }
                                        }
                                ) {
                                    Text(
                                        text = article?.source ?: "",
                                        style = MaterialTheme.typography.bodyLarge
                                    )
                                }
                                Box(
                                    modifier = Modifier
                                        .size(4.dp)
                                        .clip(CircleShape)
                                        .background(MaterialTheme.colorScheme.onSurface),
                                )
                                Text(
                                    text = article?.publishedAt?.toRelativeArticleTime() ?: "",
                                    style = MaterialTheme.typography.bodyLarge
                                )
                            }
                        }
                        HorizontalDivider(
                            modifier = Modifier.padding(bottom = 12.dp, top = 6.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.onSurface.copy(0.7f)
                        )
                        // Content
                        if (isLoading) {
                            repeat(5) {
                                ShimmerItem(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .requiredHeight(24.dp),
                                    isLoading = true,
                                    cornerRadius = 3.dp
                                ) {}
                            }
                        } else {
                            Text(
                                modifier = Modifier.fillMaxWidth(),
                                text = article?.content ?: "",
                                style = MaterialTheme.typography.bodyLarge.copy(
                                    letterSpacing = TextUnit.Unspecified
                                ),
                                textAlign = TextAlign.Justify
                            )
                        }
                        Spacer(
                            modifier = Modifier.requiredHeight(72.dp)
                        )
                    }
                }
                // Back button
                IconButton(
                    modifier = Modifier
                        .padding(12.dp)
                        .size(48.dp)
                        .clip(CircleShape)
                        .align(Alignment.TopStart),
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
            }
            // Bottom Bar
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .requiredHeight(72.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(3.dp)
                        .background(
                            Brush.verticalGradient(
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
                        .background(MaterialTheme.colorScheme.surface),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    HorizontalDivider(
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(0.2f),
                    )
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(start = 10.dp, end = 10.dp, bottom = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        // Info
                        TextButton(
                            //modifier = Modifier.size(42.dp),
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
                            onClick = {
                                dialogContent = PostDetailsDialogContent.Details
                                isDialogVisible = true
                            },
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    modifier = Modifier.size(22.dp),
                                    imageVector = Heroicons.Outline.InformationCircle,
                                    contentDescription = null,
                                )
                                Text(
                                    text = "Details", // TODO: stringResource
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                        }
                        // Tags
                        TextButton(
                            //modifier = Modifier.size(42.dp),
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
                            onClick = {
                                dialogContent = PostDetailsDialogContent.Tags
                                isDialogVisible = true
                            },
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    modifier = Modifier.size(22.dp),
                                    imageVector = Heroicons.Outline.Tag,
                                    contentDescription = null,
                                )
                                Text(
                                    text = "Tags", // TODO: stringResource
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                        }
                        // External
                        TextButton(
                            //modifier = Modifier.size(42.dp),
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
                            onClick = {
                                onNavigationEvent(MainNavigationEvent.OpenCustomTab(article?.url))
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
                                    text = "Visit Source", // TODO: stringResource
                                    style = MaterialTheme.typography.bodyMedium
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
                            .fillMaxWidth(0.95f)
                            .requiredHeight(356.dp)
                            .clip(RoundedCornerShape(5.dp))
                            .background(MaterialTheme.colorScheme.surface)
                            .padding(24.dp),
                        verticalArrangement = Arrangement.spacedBy(18.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = when (dialogContent) {
                                PostDetailsDialogContent.Details -> "Details" // TODO: stringResource
                                PostDetailsDialogContent.Tags -> "Keywords" // TODO: stringResource
                            },
                            style = MaterialTheme.typography.titleLarge
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
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "Author", // TODO: stringResource
                                        style = MaterialTheme.typography.bodyLarge,
                                    )
                                    Text(
                                        text = "John Doe", // TODO: user article field
                                        style = MaterialTheme.typography.bodyLarge,
                                    )
                                }
                            }

                            PostDetailsDialogContent.Tags -> {
                                LazyColumn(
                                    modifier = Modifier.fillMaxSize(),
                                ) {
                                    // TODO: loop through dynamic keywords field
                                    items(5) { index ->
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                text = "Tag #${index + 1}",
                                                style = MaterialTheme.typography.labelMedium
                                            )
                                            IconButton(
                                                modifier = Modifier.size(22.dp),
                                                onClick = {
                                                    // TODO: mute keyword
                                                }
                                            ) {
                                                Icon(
                                                    modifier = Modifier.size(20.dp),
                                                    imageVector = Heroicons.Outline.SpeakerXMark,
                                                    contentDescription = null // TODO
                                                )
                                            }
                                        }
                                        HorizontalDivider(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(vertical = 12.dp),
                                            thickness = 1.dp,
                                            color = MaterialTheme.colorScheme.onSurface.copy(0.125f),
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
}

@PreviewLightDark
@Composable
fun PostDetailsScreenPreview(
    @PreviewParameter(PostDetailsStateProvider::class) state: PostDetailsState
) {
    BrieflyTheme {
        Surface {
            UiStateContainer(
                modifier = Modifier.fillMaxSize(),
                state = state.details
            ) { data, isLoading ->
                PostDetailsScreen(
                    modifier = Modifier.fillMaxSize(),
                    article = data,
                    isLoading =  isLoading
                ) {}
            }
        }
    }
}
