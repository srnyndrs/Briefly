package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.XMark
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesState
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.preview.FeedSourcesStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun BlockedSourcesSection(
    modifier: Modifier = Modifier,
    blockedSources: List<Source>,
    enabled: Boolean,
    onUnblock: (String) -> Unit)
{
    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        if (blockedSources.isEmpty()) {
            Text(
                stringResource(R.string.settings_sources_empty),
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        blockedSources.forEach { source ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 48.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = source.title
                    )
                    Text(
                        text = source.url.substringAfter("//").substringBefore('/'),
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                IconButton(
                    enabled = enabled,
                    onClick = { onUnblock(source.id) }
                ) {
                    Icon(
                        imageVector = Heroicons.Solid.XMark,
                        stringResource(R.string.settings_remove_source)
                    )
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun BlockedSourcesSectionPreview(
    @PreviewParameter(FeedSourcesStateProvider::class) state: FeedSourcesState
) {
    BrieflyTheme {
        Surface {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                if (state.results is UiState.Success) {
                    BlockedSourcesSection(
                        modifier = Modifier.fillMaxWidth(),
                        blockedSources = state.results.data,
                        enabled = false,
                    ) {}
                }
            }
        }
    }
}
