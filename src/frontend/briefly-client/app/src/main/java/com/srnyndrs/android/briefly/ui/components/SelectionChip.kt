package com.srnyndrs.android.briefly.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
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
    val contentColor = MaterialTheme.colorScheme.onSurface

    ShimmerItem(
        modifier = if (isLoading) {
            Modifier
                .then(modifier)
                .size(
                    width = 96.dp,
                    height = 48.dp,
                )
        } else {
            Modifier.then(modifier)
        },
        isLoading = isLoading,
        cornerRadius = 24.dp,
    ) {
        Box(
            modifier = Modifier
                .defaultMinSize(minHeight = 48.dp)
                .clip(shape = shape)
                .border(
                    width = 1.dp,
                    color = contentColor,
                    shape = shape,
                )
                .background(
                    color = if (selected) contentColor.copy(alpha = 0.2f)
                    else MaterialTheme.colorScheme.surface,
                )
                .selectable(
                    selected = selected,
                    onClick = onClick,
                )
                .padding(
                    vertical = 8.dp,
                    horizontal = 12.dp,
                ),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColor,
            )
        }
    }
}

@PreviewLightDark
@Composable
private fun SelectionChipPreview() {
    BrieflyTheme {
        Surface {
            Row(
                modifier = Modifier.padding(all = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(space = 12.dp),
            ) {
                SelectionChip(
                    label = "Science",
                    selected = true,
                    onClick = {},
                )
                SelectionChip(
                    label = "Health",
                    selected = false,
                    onClick = {},
                )
                SelectionChip(
                    label = "",
                    selected = false,
                    isLoading = true,
                    onClick = {},
                )
            }
        }
    }
}
