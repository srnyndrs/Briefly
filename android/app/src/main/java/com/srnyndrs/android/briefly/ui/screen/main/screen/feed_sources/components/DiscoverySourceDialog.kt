package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.layout.ContentScale
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.Photo
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun DiscoverySourceDialog(
    modifier: Modifier = Modifier,
    source: SourceDiscoveryResult,
    addition: UiState<String>,
    isDuplicate: Boolean,
    onUpdate: (SourceDiscoveryResult) -> Unit,
    onDismiss: () -> Unit,
    onAdd: () -> Unit,
) {
    val canEdit = addition !is UiState.Loading && addition !is UiState.Success
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier.then(modifier),
            shape = MaterialTheme.shapes.extraLarge,
        ) {
            Column(
                modifier = Modifier
                    .verticalScroll(state = rememberScrollState())
                    .padding(all = 24.dp),
                verticalArrangement = Arrangement.spacedBy(space = 16.dp),
            ) {
                Text(
                    text = stringResource(id = R.string.feed_sources_add),
                    style = MaterialTheme.typography.headlineSmall,
                )
                Column(
                    verticalArrangement = Arrangement.spacedBy(space = 12.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(space = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        if (source.faviconUrl != null) {
                            RemoteImageContainer(
                                modifier = Modifier.size(size = 48.dp),
                                imageUrl = source.faviconUrl,
                                contentDescription = null,
                                contentScale = ContentScale.Fit,
                            )
                        } else {
                            Icon(
                                modifier = Modifier.size(size = 48.dp),
                                imageVector = Heroicons.Solid.Photo,
                                contentDescription = null,
                            )
                        }
                        Text(
                            modifier = Modifier.weight(weight = 1f),
                            text = source.url,
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    OutlinedTextField(
                        value = source.title,
                        onValueChange = { onUpdate(source.copy(title = it)) },
                        label = { Text(text = stringResource(id = R.string.feed_sources_form_title)) },
                        enabled = canEdit,
                        singleLine = true,
                    )
                    OutlinedTextField(
                        value = source.siteName.orEmpty(),
                        onValueChange = { onUpdate(source.copy(siteName = it.takeIf { value -> value.isNotBlank() })) },
                        label = { Text(text = stringResource(id = R.string.feed_sources_form_site_name)) },
                        enabled = canEdit,
                        singleLine = true,
                    )
                    OutlinedTextField(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(height = 140.dp),
                        value = source.description.orEmpty(),
                        onValueChange = { onUpdate(source.copy(description = it.takeIf { value -> value.isNotBlank() })) },
                        label = { Text(text = stringResource(id = R.string.feed_sources_form_description)) },
                        enabled = canEdit,
                        singleLine = false,
                    )
                }
                if (addition is UiState.Error) {
                    Text(
                        text = stringResource(id = if (isDuplicate) {
                            R.string.feed_sources_duplicate
                        } else R.string.feed_sources_add_error),
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    TextButton(onClick = onDismiss) {
                        Text(text = stringResource(id = R.string.feed_sources_close))
                    }
                    Button(
                        enabled = canEdit && source.title.isNotBlank() && source.title.length <= 255,
                        onClick = onAdd,
                    ) {
                        Text(text = stringResource(id = if (addition is UiState.Loading) {
                            R.string.feed_sources_adding
                        } else R.string.feed_sources_add))
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
private fun DiscoverySourceDialogPreview() {
    BrieflyTheme {
        DiscoverySourceDialog(
            source = SourceDiscoveryResult(
                url = "https://telex.hu/rss",
                title = "Telex.hu",
                description = "Latest news from Telex.",
                siteUrl = "https://telex.hu",
                language = "hu",
            ),
            addition = UiState.Idle,
            isDuplicate = false,
            onUpdate = {},
            onDismiss = {},
            onAdd = {},
        )
    }
}
