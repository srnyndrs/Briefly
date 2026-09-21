package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.SectionHeader
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components.*
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    state: UiState<SettingsUiModel> = UiState.Idle,
    onEvent: (SettingsEvent) -> Unit = {}
) {
    Column(
        modifier = Modifier.then(modifier)
    ) {
        when(state) {
            UiState.Idle, UiState.Loading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }

            is UiState.Error -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = state.message
                    )
                    Button(
                        onClick = {
                            onEvent(SettingsEvent.RetryLoad)
                        }
                    ) {
                        Text(
                            text = stringResource(R.string.session_retry)
                        )
                    }
                }
            }

            is UiState.Success -> {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(20.dp),
                    verticalArrangement = Arrangement.spacedBy(20.dp)
                ) {
                    val model = state.data
                    item {
                        Text(
                            text = stringResource(R.string.settings_title),
                            style = MaterialTheme.typography.headlineMedium)
                        Text(
                            text = stringResource(R.string.settings_subtitle)
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
                        ) { onEvent(SettingsEvent.ToggleLanguage(it)) }
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
            }
        }
    }
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
