package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PostCategoryChips(
    modifier: Modifier = Modifier,
    categories: List<String>,
) {
    if (categories.isEmpty()) return

    FlowRow(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        categories.forEach { category ->
            Surface(
                shape = RoundedCornerShape(5.dp),
                color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f),
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
            ) {
                Text(
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    text = category,
                    style = MaterialTheme.typography.labelMedium,
                )
            }
        }
    }
}

@PreviewLightDark
@Composable
fun PostCategoryChipsPreview() {
    BrieflyTheme {
        PostCategoryChips(categories = listOf("science", "health"))
    }
}
