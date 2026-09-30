package com.srnyndrs.android.briefly.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SelectionChip(
    modifier: Modifier = Modifier,
    label: String,
    selected: Boolean,
    isLoading: Boolean = false,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(24.dp)
    val contentColor = if (isLoading) Color.Transparent else MaterialTheme.colorScheme.onSurface
    ShimmerItem(modifier = modifier, isLoading = isLoading, cornerRadius = 24.dp) {
        Box(
            modifier = Modifier
                .wrapContentSize()
                .clip(shape)
                .border(1.dp, if (isLoading) Color.Transparent else contentColor, shape)
                .background(
                    if (selected || isLoading) MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f)
                    else MaterialTheme.colorScheme.surface,
                )
                .clickable(enabled = !isLoading, onClick = onClick)
                .padding(vertical = 8.dp, horizontal = 12.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(text = label, style = MaterialTheme.typography.bodyLarge, color = contentColor)
        }
    }
}

@PreviewLightDark
@Composable
private fun SelectionChipPreview() {
    BrieflyTheme {
        Surface {
            Row(
                modifier = Modifier.wrapContentWidth().padding(6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                SelectionChip(label = "Economics", selected = true) {}
                SelectionChip(label = "Politics", selected = false) {}
            }
        }
    }
}
