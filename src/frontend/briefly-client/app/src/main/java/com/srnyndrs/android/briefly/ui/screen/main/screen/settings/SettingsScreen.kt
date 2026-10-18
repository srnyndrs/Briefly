package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.SectionHeader
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.BlockedSourcesSection
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.LanguageSelectionList
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.PreferenceKeywordInput
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    state: UiState<SettingsUiModel> = UiState.Idle,
    onEvent: (SettingsEvent) -> Unit = {},
) {
    UiStateContainer(
        modifier = modifier,
        state = state,
        idle = { CircularProgressIndicator() },
        loading = { CircularProgressIndicator() },
        error = { message ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(text = message)
                Button(onClick = { onEvent(SettingsEvent.RetryLoad) }) {
                    Text(text = stringResource(R.string.session_retry))
                }
            }
        },
        success = { model ->
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(20.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                item {
                    Text(
                        text = stringResource(R.string.settings_title),
                        style = MaterialTheme.typography.headlineMedium
                    )
                    HorizontalDivider(
                        modifier = Modifier.padding(top = 16.dp),
                        thickness = 2.dp
                    )
                }
                item {
                    SectionHeader(
                        title = stringResource(R.string.settings_section_languages),
                        subtitle = stringResource(R.string.settings_languages_description)
                    )
                    LanguageSelectionList(
                        modifier = Modifier.padding(top = 8.dp),
                        options = model.languageOptions,
                        selectedCodes = model.selectedLanguageCodes,
                        enabled = !model.isUpdating
                    ) {
                        onEvent(SettingsEvent.ToggleLanguage(it))
                    }
                }
                item {
                    SectionHeader(
                        title = stringResource(R.string.settings_section_categories),
                        subtitle = stringResource(R.string.settings_categories_description)
                    )
                    model.mutedCategories.forEach { category ->
                        AssistChip(
                            enabled = !model.isUpdating,
                            onClick = {
                                onEvent(SettingsEvent.RemoveMutedCategory(category))
                            },
                            label = {
                                Text(text = category)
                            }
                        )
                    }
                }
                item {
                    SectionHeader(
                        title = stringResource(R.string.settings_section_keywords),
                        subtitle = stringResource(R.string.settings_keywords_description)
                    )
                    PreferenceKeywordInput(
                        modifier = Modifier.padding(top = 8.dp),
                        value = model.keywordDraft,
                        keywords = model.mutedKeywords,
                        onValueChange = {
                            onEvent(SettingsEvent.KeywordDraftChanged(it))
                        },
                        onAdd = {
                            onEvent(SettingsEvent.AddMutedKeyword)
                        },
                        onRemove = {
                            onEvent(SettingsEvent.RemoveMutedKeyword(it))
                        }
                    )
                }
                item {
                    SectionHeader(
                        title = stringResource(R.string.settings_section_sources),
                        subtitle = stringResource(R.string.settings_sources_description)
                    )
                    BlockedSourcesSection(
                        modifier = Modifier.padding(top = 8.dp),
                        blockedSources = model.blockedSources,
                        enabled = !model.isUpdating
                    ) {
                        onEvent(SettingsEvent.UnblockSource(it))
                    }
                }
                item {
                    model.errorMessage?.let {
                        Text(
                            text = it,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                    if(model.isUpdating) {
                        LinearProgressIndicator(
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
        },
    )
}

@PreviewLightDark
@Composable
fun SettingsScreenPreview() {
    BrieflyTheme {
        Surface {
            SettingsScreen(
                modifier = Modifier.fillMaxSize(),
                state = UiState.Success(
                    data = SettingsUiModel(

                    )
                )
            ) {}
        }
    }
}
