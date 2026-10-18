package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PostItemCardPlaceholder(modifier: Modifier = Modifier) {
    ShimmerGroup {
        Row(
            modifier = modifier
                .fillMaxWidth()
                .height(128.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxSize()
                    .padding(8.dp),
                verticalArrangement = Arrangement.SpaceBetween,
            ) {
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(36.dp),
                    isLoading = true,
                    cornerRadius = 5.dp,
                ) {}
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(24.dp),
                    isLoading = true,
                    cornerRadius = 5.dp,
                ) {}
                // One placeholder covers the complete date unit, including its calendar icon.
                ShimmerItem(
                    modifier = Modifier
                        .width(96.dp)
                        .height(18.dp),
                    isLoading = true,
                    cornerRadius = 5.dp,
                ) {}
            }
            ShimmerItem(
                modifier = Modifier.size(128.dp),
                isLoading = true,
                cornerRadius = 5.dp,
            ) {}
        }
    }
}

@PreviewLightDark
@Composable
private fun PostItemCardPlaceholderPreview() {
    BrieflyTheme {
        Surface {
            PostItemCardPlaceholder()
        }
    }
}
