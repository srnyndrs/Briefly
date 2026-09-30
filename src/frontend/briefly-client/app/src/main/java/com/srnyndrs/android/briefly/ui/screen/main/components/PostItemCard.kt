package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Calendar
import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.screen.main.components.preview.PostPreviewProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
@Composable
fun PostItemCard(
    modifier: Modifier = Modifier,
    title: String,
    categories: List<Category> = emptyList(),
    description: String,
    imageUrl: String? = null,
    publishedAt: Instant? = null,
    onClick: (() -> Unit)? = null,
) {
    val shape = RoundedCornerShape(size = 5.dp)
    val image = imageUrl?.takeIf { it.isNotBlank() }

    Row(
        modifier = Modifier
            .then(modifier)
            .height(height = 128.dp)
            .clip(shape = shape)
            .border(
                width = 1.dp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f),
                shape = shape,
            )
            .let {
                if (onClick != null) it.clickable(
                    role = Role.Button,
                    onClick = onClick,
                ) else it
            },
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(
            modifier = Modifier
                .weight(weight = 1f)
                .fillMaxHeight()
                .padding(
                    horizontal = 6.dp,
                    vertical = 8.dp,
                ),
            verticalArrangement = Arrangement.spacedBy(space = 6.dp),
        ) {
            Text(
                modifier = Modifier.weight(weight = 1f),
                text = title,
                style = MaterialTheme.typography.titleSmall,
                overflow = TextOverflow.Ellipsis,
                minLines = 1,
                maxLines = 3,
            )
            if (categories.isNotEmpty()) {
                PostCategoryChips(
                    categories = categories,
                    maxLines = 1,
                )
            } else if (description.isNotBlank()) {
                Text(
                    modifier = Modifier.weight(weight = 1f),
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    overflow = TextOverflow.Ellipsis,
                    maxLines = 2,
                )
            }
            if (publishedAt != null) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(space = 6.dp),
                ) {
                    Icon(
                        modifier = Modifier.size(size = 18.dp),
                        imageVector = Heroicons.Outline.Calendar,
                        contentDescription = null,
                    )
                    Text(
                        text = publishedAt.toRelativeArticleTime(),
                        style = MaterialTheme.typography.labelSmall,
                    )
                }
            }
        }
        if (image != null) {
            RemoteImageContainer(
                modifier = Modifier
                    .fillMaxHeight()
                    .aspectRatio(ratio = 1f),
                imageUrl = image,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                enableFade = true,
            )
        }
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun PostItemCardPreview(
    @PreviewParameter(PostPreviewProvider::class) post: Post,
) {
    BrieflyTheme {
        Surface {
            PostItemCard(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(all = 6.dp),
                title = post.title,
                categories = post.categories,
                description = post.description.orEmpty(),
                imageUrl = post.imageUrl,
                publishedAt = post.publishedAt,
                onClick = {},
            )
        }
    }
}
