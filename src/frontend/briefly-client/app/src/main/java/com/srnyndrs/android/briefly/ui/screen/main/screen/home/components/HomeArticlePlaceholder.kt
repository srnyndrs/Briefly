package com.srnyndrs.android.briefly.ui.screen.main.screen.home.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun HomeArticlePlaceholder(modifier: Modifier = Modifier) {
    Column(
        modifier = Modifier
            .then(modifier)
            .padding(vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(space = 12.dp),
    ) {
        ShimmerItem(
            modifier = Modifier
                .fillMaxWidth(fraction = 0.25f)
                .height(height = 16.dp),
            isLoading = true,
            cornerRadius = 3.dp,
        ) {}
        repeat(times = 2) {
            ShimmerItem(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(height = 24.dp),
                isLoading = true,
                cornerRadius = 3.dp,
            ) {}
        }
    }
}

@PreviewLightDark
@Composable
private fun HomeArticlePlaceholderPreview() {
    BrieflyTheme {
        Surface {
            HomeArticlePlaceholder(modifier = Modifier.fillMaxWidth())
        }
    }
}
