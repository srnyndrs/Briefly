package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun FeedSourceResultsPlaceholder() {
    ShimmerGroup {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(space = 22.dp),
        ) {
            items(count = 3) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(height = 64.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
                ) {
                    ShimmerItem(
                        modifier = Modifier.size(size = 64.dp),
                        isLoading = true,
                        cornerRadius = 5.dp,
                    ) {}
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                    ) {
                        repeat(times = 2) {
                            ShimmerItem(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .defaultMinSize(minHeight = 28.dp),
                                isLoading = true,
                                cornerRadius = 5.dp,
                            ) {}
                        }
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
private fun FeedSourceResultsPlaceholderPreview() {
    BrieflyTheme { FeedSourceResultsPlaceholder() }
}
