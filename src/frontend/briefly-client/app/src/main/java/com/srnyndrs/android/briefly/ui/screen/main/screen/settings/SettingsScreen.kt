package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.XMark
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.SectionHeader
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.BlockedSourcesSection
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.LanguageSelectionList
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.PreferenceKeywordInput
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.preview.SettingsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    state: UiState<SettingsUiModel>,
    onEvent: (SettingsEvent) -> Unit,
) {
    UiStateContainer(
        modifier = Modifier.then(modifier),
        state = state,
        idle = { CircularProgressIndicator() },
        loading = { CircularProgressIndicator() },
        error = {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(all = 24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(text = stringResource(id = R.string.settings_load_error))
                Button(onClick = { onEvent(SettingsEvent.RetryLoad) }) {
                    Text(text = stringResource(id = R.string.session_retry))
                }
            }
        },
        success = { model ->
            Column(modifier = Modifier.fillMaxSize()) {
                if (model.isUpdating) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(all = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                    ) {
                        Text(text = stringResource(id = R.string.settings_saving))
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    }
                }
                if (model.updateFailed) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(all = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(space = 8.dp),
                    ) {
                        Text(
                            text = stringResource(id = R.string.settings_failure),
                            color = MaterialTheme.colorScheme.error,
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(space = 8.dp)) {
                            Button(onClick = { onEvent(SettingsEvent.RetryUpdate) }) {
                                Text(text = stringResource(id = R.string.session_retry))
                            }
                            TextButton(onClick = { onEvent(SettingsEvent.DismissError) }) {
                                Text(text = stringResource(id = R.string.settings_dismiss))
                            }
                        }
                    }
                }
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(weight = 1f),
                    contentPadding = PaddingValues(all = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(space = 20.dp),
                ) {
                    item(key = "title") {
                        Text(
                            text = stringResource(id = R.string.settings_title),
                            style = MaterialTheme.typography.headlineMedium,
                        )
                        HorizontalDivider(
                            modifier = Modifier.padding(top = 16.dp),
                            thickness = 2.dp,
                        )
                    }
                    item(key = "languages") {
                        SectionHeader(
                            title = stringResource(id = R.string.settings_section_languages),
                            subtitle = stringResource(id = R.string.settings_languages_description),
                        )
                        LanguageSelectionList(
                            modifier = Modifier.padding(top = 8.dp),
                            options = model.languageOptions,
                            selectedCodes = model.selectedLanguageCodes,
                            enabled = !model.isUpdating,
                            onToggle = { onEvent(SettingsEvent.ToggleLanguage(code = it)) },
                        )
                    }
                    item(key = "categories") {
                        SectionHeader(
                            title = stringResource(id = R.string.settings_section_categories),
                            subtitle = stringResource(id = R.string.settings_categories_description),
                        )
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
                            verticalArrangement = Arrangement.spacedBy(space = 4.dp),
                        ) {
                            model.mutedCategories.forEach { category ->
                                val removeDescription = stringResource(
                                    id = R.string.settings_unmute_category,
                                    category,
                                )
                                AssistChip(
                                    modifier = Modifier.semantics { contentDescription = removeDescription },
                                    enabled = !model.isUpdating,
                                    onClick = { onEvent(SettingsEvent.RemoveMutedCategory(category = category)) },
                                    label = { Text(text = category) },
                                    trailingIcon = {
                                        Icon(
                                            imageVector = Heroicons.Solid.XMark,
                                            contentDescription = null,
                                        )
                                    },
                                )
                            }
                        }
                    }
                    item(key = "keywords") {
                        SectionHeader(
                            title = stringResource(id = R.string.settings_section_keywords),
                            subtitle = stringResource(id = R.string.settings_keywords_description),
                        )
                        PreferenceKeywordInput(
                            modifier = Modifier.padding(top = 8.dp),
                            value = model.keywordDraft,
                            keywords = model.mutedKeywords,
                            enabled = !model.isUpdating,
                            onValueChange = { onEvent(SettingsEvent.KeywordDraftChanged(value = it)) },
                            onAdd = { onEvent(SettingsEvent.AddMutedKeyword) },
                            onRemove = { onEvent(SettingsEvent.RemoveMutedKeyword(keyword = it)) },
                        )
                    }
                    item(key = "sources") {
                        SectionHeader(
                            title = stringResource(id = R.string.settings_section_sources),
                            subtitle = stringResource(id = R.string.settings_sources_description),
                        )
                        BlockedSourcesSection(
                            modifier = Modifier.padding(top = 8.dp),
                            blockedSources = model.blockedSources,
                            enabled = !model.isUpdating,
                            onUnblock = { onEvent(SettingsEvent.UnblockSource(sourceId = it)) },
                        )
                    }
                }
            }
        },
    )
}

@PreviewLightDark
@Composable
fun SettingsScreenPreview(
    @PreviewParameter(SettingsStateProvider::class) state: UiState<SettingsUiModel>,
) {
    BrieflyTheme {
        Surface {
            SettingsScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onEvent = {},
            )
        }
    }
}
