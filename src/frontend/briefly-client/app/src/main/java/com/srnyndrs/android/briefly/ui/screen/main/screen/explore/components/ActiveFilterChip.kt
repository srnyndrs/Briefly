package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.XMark
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ActiveFilterChip(
    modifier: Modifier = Modifier,
    label: String,
    onRemove: () -> Unit,
) {
    val shape = RoundedCornerShape(20.dp)
    val contentColor = MaterialTheme.colorScheme.onSurface

    Box(
        modifier = modifier
            .wrapContentSize()
            .clip(shape)
            .border(
                width = 1.dp,
                color = contentColor.copy(alpha = 0.6f),
                shape = shape,
            )
            .background(MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f))
            .clickable(onClick = onRemove)
            .padding(horizontal = 10.dp, vertical = 6.dp),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                color = contentColor,
            )
            Icon(
                modifier = Modifier.size(16.dp),
                imageVector = Heroicons.Solid.XMark,
                contentDescription = null,
                tint = contentColor.copy(alpha = 0.7f),
            )
        }
    }
}

@PreviewLightDark
@Composable
fun ActiveFilterChipPreview() {
    BrieflyTheme {
        Surface {
            ActiveFilterChip(
                modifier = Modifier.padding(16.dp),
                label = "Politics",
                onRemove = {},
            )
        }
    }
}

