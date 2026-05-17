package com.srnyndrs.android.briefly.ui.screen.content.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.ContentExploreState
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.preview.ContentExploreStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ArticleRow(
    modifier: Modifier = Modifier,
    title: String,
    source: String?,
    description: String?,
    tag: String?,
    onClick: () -> Unit
) {
    Column(
        modifier = Modifier.then(modifier)
            .clickable {
                onClick()
            },
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Source
        source?.let { sourceTitle ->
            Row(
                modifier = Modifier.wrapContentWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                // Favicon
                /*RemoteImageContainer(
                    modifier = Modifier
                        .size(24.dp)
                        .clip(CircleShape),
                    imageUrl = "", // TODO
                    contentScale = ContentScale.Fit
                )*/
                // Source name
                Text(
                    text = sourceTitle,
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }
        }
        // Category Tag
        /*Row(
            modifier = Modifier
                .wrapContentWidth()
                .clip(RoundedCornerShape(5.dp))
                .background(
                    // TODO
                    Color(0xFF124578)
                )
        ) {
            Text(
                modifier = Modifier.padding(3.dp),
                text = tag,
                style = MaterialTheme.typography.labelMedium,
                // TODO
                color = MaterialTheme.colorScheme.surface
            )
        }*/
        // Title
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = title,
            minLines = 1,
            textAlign = TextAlign.Start,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Black,
            overflow = TextOverflow.Ellipsis
        )
        // Description
        /*description?.let {
            Text(
                modifier = Modifier.fillMaxWidth(),
                text = it,
                minLines = 1,
                maxLines = 2,
                style = MaterialTheme.typography.bodyMedium,
                overflow = TextOverflow.Ellipsis,
            )
        }*/
    }
}

@PreviewLightDark
@Composable
fun ArticleRowPreview(
    @PreviewParameter(ContentExploreStateProvider::class) state: ContentExploreState
) {
    val articles = (state.result as UiState.Success).data.items
    BrieflyTheme {
        Surface(
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                articles.map { article ->
                    ArticleRow(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp, horizontal = 6.dp),
                        title = article.title,
                        source = "24.hu",
                        description = article.description,
                        tag = "Belföld"
                    ) {}
                }
            }
        }
    }
}
