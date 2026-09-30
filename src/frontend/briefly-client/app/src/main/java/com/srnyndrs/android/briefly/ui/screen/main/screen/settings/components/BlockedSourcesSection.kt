package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.XMark
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.preview.SettingsPreviewData
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun BlockedSourcesSection(
    modifier: Modifier = Modifier,
    blockedSources: List<Source>,
    enabled: Boolean,
    onUnblock: (String) -> Unit,
) {
    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(space = 4.dp),
    ) {
        if (blockedSources.isEmpty()) {
            Text(
                text = stringResource(id = R.string.settings_sources_empty),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        blockedSources.forEach { source ->
            val title = source.title.ifBlank { stringResource(id = R.string.settings_unavailable_source) }
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 48.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(weight = 1f)) {
                    Text(text = title)
                    if (source.url.isNotBlank()) {
                        Text(
                            text = source.url.substringAfter(delimiter = "//").substringBefore(delimiter = '/'),
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
                IconButton(
                    enabled = enabled,
                    onClick = { onUnblock(source.id) },
                ) {
                    Icon(
                        imageVector = Heroicons.Solid.XMark,
                        contentDescription = stringResource(
                            id = R.string.settings_unblock_source,
                            title,
                        ),
                    )
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun BlockedSourcesSectionPreview() {
    BrieflyTheme {
        Surface {
            BlockedSourcesSection(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(all = 12.dp),
                blockedSources = SettingsPreviewData.model.blockedSources,
                enabled = true,
                onUnblock = {},
            )
        }
    }
}
