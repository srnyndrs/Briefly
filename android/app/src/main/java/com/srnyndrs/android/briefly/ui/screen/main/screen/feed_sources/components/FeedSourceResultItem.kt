package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.CheckBadge
import com.composables.icons.heroicons.solid.Photo
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun FeedSourceResultItem(
    modifier: Modifier = Modifier,
    title: String,
    url: String,
    faviconUrl: String?,
    verified: Boolean = false,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .then(modifier)
            .fillMaxWidth()
            .requiredHeight(height = 64.dp)
            .clickable(onClick = onClick),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Row(
            modifier = Modifier.weight(weight = 0.8f),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
        ) {
            Box(
                modifier = Modifier.size(size = 64.dp),
                contentAlignment = Alignment.Center,
            ) {
                if (faviconUrl != null) {
                    RemoteImageContainer(
                        modifier = Modifier.fillMaxSize(),
                        imageUrl = faviconUrl,
                        contentDescription = null,
                        contentScale = ContentScale.Fit,
                    )
                } else {
                    Icon(
                        modifier = Modifier.size(size = 64.dp),
                        imageVector = Heroicons.Solid.Photo,
                        contentDescription = null,
                    )
                }
            }
            Column(verticalArrangement = Arrangement.spacedBy(space = 3.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(space = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        modifier = Modifier.weight(weight = 1f),
                        text = title,
                        minLines = 1,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        style = MaterialTheme.typography.bodyLarge.copy(
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Medium,
                        ),
                    )
                    if (verified) {
                        Icon(
                            modifier = Modifier.size(size = 22.dp),
                            imageVector = Heroicons.Outline.CheckBadge,
                            tint = MaterialTheme.colorScheme.primary,
                            contentDescription = stringResource(id = R.string.feed_sources_verified),
                        )
                    }
                }
                Text(
                    modifier = Modifier.fillMaxWidth(),
                    text = url,
                    minLines = 1,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    style = MaterialTheme.typography.labelLarge,
                )
            }
        }
    }
}

@PreviewLightDark
@Composable
private fun FeedSourceResultItemPreview() {
    BrieflyTheme {
        FeedSourceResultItem(
            title = "Telex.hu",
            url = "https://telex.hu/rss",
            faviconUrl = null,
            verified = true,
            onClick = {},
        )
    }
}
