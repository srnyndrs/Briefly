package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.screen.main.components.preview.PostPreviewProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlin.time.ExperimentalTime

@Composable
fun PostCard(
    modifier: Modifier = Modifier,
    title: String,
    description: String,
    imageUrl: String? = null,
    isLoading: Boolean = false,
    onClick: (() -> Unit)? = null,
) {
    if (isLoading) {
        ShimmerGroup {
            Row(
                modifier = Modifier
                    .then(modifier)
                    .fillMaxWidth()
                    .padding(vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
            ) {
                ShimmerItem(
                    modifier = Modifier
                        .weight(weight = 1f)
                        .aspectRatio(ratio = 16f / 9f),
                    isLoading = true,
                ) {}
                Column(
                    modifier = Modifier.weight(weight = 2f),
                    verticalArrangement = Arrangement.spacedBy(space = 4.dp),
                ) {
                    repeat(times = 2) { index ->
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(height = if (index == 0) 32.dp else 48.dp),
                            isLoading = true,
                            cornerRadius = 5.dp,
                        ) {}
                    }
                }
            }
        }
        return
    }

    Row(
        modifier = Modifier
            .then(modifier)
            .fillMaxWidth()
            .defaultMinSize(minHeight = 72.dp)
            .let {
                if (onClick != null) it.clickable(
                    role = Role.Button,
                    onClick = onClick,
                ) else it
            }
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.Top,
        horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
    ) {
        imageUrl?.takeIf { it.isNotBlank() }?.let { image ->
            RemoteImageContainer(
                modifier = Modifier
                    .weight(weight = 1f)
                    .aspectRatio(ratio = 16f / 9f)
                    .background(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f))
                    .border(
                        width = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface,
                        shape = RectangleShape,
                    ),
                imageUrl = image,
                contentDescription = null,
            )
        }
        Column(
            modifier = Modifier.weight(weight = 2f),
            verticalArrangement = Arrangement.spacedBy(space = 4.dp),
        ) {
            Text(
                modifier = Modifier.fillMaxWidth(),
                text = title,
                style = MaterialTheme.typography.titleMedium,
                minLines = 1,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            if (description.isNotBlank()) {
                Text(
                    modifier = Modifier.fillMaxWidth(),
                    text = description,
                    maxLines = 3,
                    style = MaterialTheme.typography.bodyMedium,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun PostCardPreview(
    @PreviewParameter(PostPreviewProvider::class) post: Post,
) {
    BrieflyTheme {
        Surface {
            PostCard(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(all = 6.dp),
                title = post.title,
                description = post.description.orEmpty(),
                imageUrl = post.imageUrl,
                onClick = {},
            )
        }
    }
}

@PreviewLightDark
@Composable
private fun PostCardLoadingPreview() {
    BrieflyTheme {
        Surface {
            PostCard(
                modifier = Modifier.fillMaxWidth(),
                title = "",
                description = "",
                isLoading = true,
            )
        }
    }
}
