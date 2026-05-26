package com.srnyndrs.android.briefly.ui.common

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonColors
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
import com.composables.icons.heroicons.solid.Bars3
import com.composables.icons.heroicons.solid.User
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun TopAppBar(
    modifier: Modifier = Modifier,
    onMenuSelect: () -> Unit,
    onProfileSelect: () -> Unit,
) {

    Column(
        modifier = Modifier.then(modifier)
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalArrangement = Arrangement.spacedBy(3.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .requiredHeight(56.dp),
            horizontalArrangement = Arrangement.Absolute.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Hamburger menu
            IconButton(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape),
                onClick = onMenuSelect,
                colors = IconButtonColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(0.7f),
                    contentColor = MaterialTheme.colorScheme.onSurface,
                    disabledContainerColor = MaterialTheme.colorScheme.surface,
                    disabledContentColor = MaterialTheme.colorScheme.onSurface
                )
            ) {
                Icon(
                    modifier = Modifier.size(32.dp),
                    imageVector = Heroicons.Solid.Bars3,
                    contentDescription = null // TODO
                )
            }
            // Title
            Text(
                text = "Briefly",
                style = MaterialTheme.typography.titleLarge,
            )
            // User settings
            IconButton(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape),
                onClick = onProfileSelect,
                enabled = true,
                colors = IconButtonColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(0.7f),
                    contentColor = MaterialTheme.colorScheme.onSurface,
                    disabledContainerColor = MaterialTheme.colorScheme.surface,
                    disabledContentColor = MaterialTheme.colorScheme.onSurface
                )
            ) {
                Icon(
                    modifier = Modifier
                        .size(32.dp)
                        .border(
                        1.dp,
                        MaterialTheme.colorScheme.onSurface,
                                CircleShape
                        )
                        .padding(3.dp),
                    imageVector = Heroicons.Solid.User,
                    contentDescription = null // TODO
                )
            }

        }
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(3.dp)
        ) {
            HorizontalDivider(
                thickness = 2.dp,
                color = MaterialTheme.colorScheme.onSurface,
            )
            HorizontalDivider(
                thickness = 4.dp,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

@PreviewLightDark
@Composable
fun TopAppBarPreview() {
    BrieflyTheme {
        Surface {
            TopAppBar(
                onMenuSelect = {},
                onProfileSelect = {}
            )
        }
    }
}