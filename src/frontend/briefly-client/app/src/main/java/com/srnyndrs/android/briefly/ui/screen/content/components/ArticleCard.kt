package com.srnyndrs.android.briefly.ui.screen.content.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.common.ShimmerItem
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme


@Composable
fun ArticleCard(
    modifier: Modifier = Modifier,
    title: String,
    description: String,
    imageUrl: String? = null,
    isLoading: Boolean = false,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .defaultMinSize(minHeight = 72.dp)
            .clickable(
                enabled = onClick !== null
            ) { onClick?.invoke() }
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.Top
    ) {
        // Image
        ShimmerItem(
            modifier = Modifier
                .let {
                    if(imageUrl != null) {
                        it.aspectRatio(16 / 9f)
                            .weight(1 / 3f)
                            .background(
                                MaterialTheme.colorScheme.onSurface.copy(0.4f)
                            )
                            .border(
                                1.dp,
                                MaterialTheme.colorScheme.onSurface,
                                RectangleShape
                            )
                    } else it.size(0.dp)
                },
            isLoading = isLoading
        ) {
            if(imageUrl != null) {
                RemoteImageContainer(
                    modifier = Modifier.fillMaxSize(),
                    imageUrl = imageUrl
                )
            }
        }
        if(imageUrl != null) {
            Spacer(
                modifier = Modifier.requiredWidth(8.dp)
            )
        }
        // Content
        Column(
            modifier = Modifier.weight(2 / 3f),
            verticalArrangement = Arrangement.Top
        ) {
            // Title
            ShimmerItem(
                modifier = Modifier
                    .fillMaxWidth()
                    .defaultMinSize(minHeight = 16.dp),
                isLoading = isLoading,
                cornerRadius = 5.dp
            ) {
                Text(
                    modifier = Modifier.fillMaxWidth(),
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    minLines = 1,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    textAlign = TextAlign.Start,
                )
            }
            Spacer(
                modifier = Modifier.requiredHeight(4.dp)
            )
            // Description
            ShimmerItem(
                modifier = Modifier
                    .fillMaxWidth()
                    .defaultMinSize(minHeight = 16.dp),
                isLoading = isLoading,
                cornerRadius = 5.dp
            ) {
                Text(
                    modifier = Modifier.fillMaxWidth(),
                    text = description,
                    minLines = 1,
                    maxLines = 3,
                    style = MaterialTheme.typography.bodyMedium,
                    overflow = TextOverflow.Ellipsis,
                    textAlign = TextAlign.Justify,
                )
            }
        }
    }
}

@PreviewLightDark
@Composable
fun ArticleCardPreview() {
    BrieflyTheme {
        Surface {
            ArticleCard(
                modifier = Modifier.fillMaxWidth().padding(6.dp),
                title = "Breaking news",
                description = "This is the description",
                imageUrl = "",
                isLoading = true
            )
        }
    }
}