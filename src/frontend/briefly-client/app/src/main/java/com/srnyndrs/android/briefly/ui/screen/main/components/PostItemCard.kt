package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Calendar
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.shimmer
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
@Composable
fun PostItemCard(
    modifier: Modifier = Modifier,
    title: String,
    categories: List<String>,
    description: String,
    imageUrl: String? = null,
    publishDate: Instant? = null,
    isLoading: Boolean = false,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = modifier
            .clickable(enabled = onClick !== null) {
                onClick?.invoke()
            },
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    1.dp,
                    MaterialTheme.colorScheme.onSurface.copy(0.4f),
                    RoundedCornerShape(5.dp)
                )
        ) {
            Column(
                modifier = Modifier.weight(0.7f)
                    .fillMaxHeight()
                    .padding(horizontal = 6.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.SpaceBetween,
                horizontalAlignment = Alignment.Start
            ) {
                if (categories.isNotEmpty()) {
                    PostCategoryChips(
                        modifier = Modifier
                            .weight(0.3f)
                            .fillMaxWidth()
                            .horizontalScroll(rememberScrollState())
                            .shimmer(isLoading),
                        categories = categories,
                    )
                }
                // Title
                Column(
                    modifier = Modifier.weight(0.4f).fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    ShimmerItem(
                        modifier = Modifier
                            .fillMaxWidth()
                            .defaultMinSize(minHeight = 28.dp),
                        isLoading = isLoading,
                        cornerRadius = 5.dp
                    ) {
                        Text(
                            text = title,
                            style = MaterialTheme.typography.titleSmall,
                            overflow = TextOverflow.Ellipsis,
                            minLines = 1,
                            maxLines = 3,
                            softWrap = true
                        )
                    }
                }
                // Description
                if (categories.isEmpty()) {
                    Column(
                        modifier = Modifier.weight(0.3f).fillMaxWidth()
                    ) {
                        Text(
                            text = description,
                            style = MaterialTheme.typography.bodySmall,
                            overflow = TextOverflow.Ellipsis,
                            minLines = 1,
                            maxLines = 3,
                            softWrap = true
                        )
                    }
                }
                Row(
                    modifier = Modifier.weight(0.2f).fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Icon(
                        modifier = Modifier.size(18.dp),
                        imageVector = Heroicons.Outline.Calendar,
                        contentDescription = null // TODO
                    )
                    ShimmerItem(
                        modifier = Modifier
                            .defaultMinSize(
                                minHeight = 16.dp,
                                minWidth = if (isLoading) 72.dp else 0.dp,
                            ),
                        isLoading = isLoading,
                        cornerRadius = 5.dp,
                        contentAlignment = Alignment.CenterStart,
                    ) {
                        Text(
                            text = publishDate?.toRelativeArticleTime() ?: "",
                            style = MaterialTheme.typography.labelSmall,
                        )
                    }
                }
            }
            Column(
                modifier = Modifier.weight(0.4f),
                verticalArrangement = Arrangement.Top,
                horizontalAlignment = Alignment.End
            ) {
                ShimmerItem(
                    modifier = Modifier
                        .let {
                            if(imageUrl != null) {
                                it.fillMaxHeight()
                                    .clip(RoundedCornerShape(
                                        bottomEnd = 5.dp,
                                        topEnd =5.dp
                                    ))
                                    .background(
                                        MaterialTheme.colorScheme.onSurface.copy(0.4f)
                                    )
                            } else it.size(0.dp)
                        },
                    isLoading = isLoading,
                    contentAlignment = Alignment.CenterEnd
                ) {
                    if(imageUrl != null) {
                        RemoteImageContainer(
                            modifier = Modifier
                                .fillMaxHeight()
                                .aspectRatio(1f),
                            contentScale = ContentScale.Crop,
                            imageUrl = imageUrl ?: "",
                            enableFade = true,
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun PostItemCardPreview() {
    BrieflyTheme {
        Surface {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 12.dp, horizontal = 6.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                PostItemCard(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(128.dp),
                    title = "A magyar néptánc még ma is tömegeket mozgat meg!",
                    categories = listOf("entertainment", "lifestyle"),
                    imageUrl = "",
                    description = "",
                    publishDate = Instant.parse("2026-09-15T18:36:11Z"),
                    isLoading = false
                ) {}
                PostItemCard(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(128.dp),
                    title = "A nap hírei összefoglalva",
                    categories = emptyList(),
                    imageUrl = "",
                    description = "Idén lett 100 éves a szakmai bizottságok meghatározó szerepét betöltő elnökség",
                    publishDate = Instant.parse("2026-09-12T18:36:11Z"),
                    isLoading = false
                ) {}
            }
        }
    }
}
