package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.BottomSheetDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
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
import androidx.compose.ui.draw.dropShadow
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
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ArrowTopRightOnSquare
import com.composables.icons.heroicons.outline.ChevronLeft
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.preview.PostDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTime::class)
@Composable
fun PostDetailsScreen(
    modifier: Modifier = Modifier,
    isLoading: Boolean = false,
    article: PostDetails?,
    onNavigationEvent: (MainNavigationEvent) -> Unit
) {

    val scrollState = rememberScrollState()

    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.TopCenter
    ) {
        Box(
            modifier = Modifier
                .align(Alignment.TopCenter)
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
                                            onNavigationEvent(MainNavigationEvent.ShowSourceDetails(it))
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
                    if(isLoading) {
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
                        .padding(start = 16.dp, end = 16.dp, bottom = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    // External
                    OutlinedIconButton(
                        modifier = Modifier.size(42.dp),
                        shape = RectangleShape,
                        enabled = !isLoading,
                        onClick = {
                            onNavigationEvent(MainNavigationEvent.OpenCustomTab(article?.url))
                        },
                    ) {
                        Icon(
                            modifier = Modifier.size(32.dp),
                            imageVector = Heroicons.Outline.ArrowTopRightOnSquare,
                            contentDescription = null,
                        )
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
                ) { }
            }
        }
    }
}
