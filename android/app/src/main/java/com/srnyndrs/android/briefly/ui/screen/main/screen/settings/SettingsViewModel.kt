package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import com.srnyndrs.android.briefly.domain.usecase.content.source.GetFeedSourcesUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetExploreFilterOptionsUseCase
import com.srnyndrs.android.briefly.domain.usecase.preferences.GetPreferencesUseCase
import com.srnyndrs.android.briefly.domain.usecase.preferences.UpdatePreferencesUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import java.util.Locale
import javax.inject.Inject
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val getPreferencesUseCase: GetPreferencesUseCase,
    private val getExploreFilterOptionsUseCase: GetExploreFilterOptionsUseCase,
    private val getFeedSourcesUseCase: GetFeedSourcesUseCase,
    private val updatePreferencesUseCase: UpdatePreferencesUseCase,
): ViewModel() {

    private val _state = MutableStateFlow<UiState<SettingsUiModel>>(value = UiState.Idle)
    val state = _state.asStateFlow()

    private var sourceCatalog: Map<String, Source> = emptyMap()
    private var availableLanguages: List<String> = emptyList()
    private var failedUpdate: ((UserPreferences) -> UserPreferences)? = null

    init {
        load()
    }

    fun onEvent(event: SettingsEvent) {
        when (event) {
            SettingsEvent.RetryLoad -> {
                if (_state.value is UiState.Error) load()
            }
            SettingsEvent.RetryUpdate -> failedUpdate?.let { updatePreferences(transform = it) }
            is SettingsEvent.ToggleLanguage -> {
                val current = (_state.value as? UiState.Success)?.data ?: return
                val code = event.code.trim().lowercase(Locale.ROOT)
                val select = code !in current.selectedLanguageCodes
                updatePreferences { preferences ->
                    preferences.copy(
                        languages = if (select) {
                            preferences.languages + code
                        } else {
                            preferences.languages.filterNot {
                                it.equals(
                                    other = code,
                                    ignoreCase = true,
                                )
                            }.toSet()
                        },
                    )
                }
            }
            is SettingsEvent.RemoveMutedCategory -> updatePreferences { preferences ->
                preferences.copy(
                    mutedCategories = preferences.mutedCategories.filterNot {
                        it.equals(
                            other = event.category,
                            ignoreCase = true,
                        )
                    },
                )
            }
            is SettingsEvent.KeywordDraftChanged -> edit {
                if (it.isUpdating) it else it.copy(keywordDraft = event.value)
            }
            SettingsEvent.AddMutedKeyword -> {
                val current = (_state.value as? UiState.Success)?.data ?: return
                val keyword = current.keywordDraft.trim()
                if (keyword.isBlank()) return
                updatePreferences { preferences ->
                    val alreadyMuted = preferences.mutedKeywords.any {
                        it.equals(
                            other = keyword,
                            ignoreCase = true,
                        )
                    }
                    if (alreadyMuted) preferences else preferences.copy(
                        mutedKeywords = preferences.mutedKeywords + keyword,
                    )
                }
            }
            is SettingsEvent.RemoveMutedKeyword -> updatePreferences { preferences ->
                preferences.copy(
                    mutedKeywords = preferences.mutedKeywords.filterNot {
                        it.equals(
                            other = event.keyword,
                            ignoreCase = true,
                        )
                    },
                )
            }
            is SettingsEvent.UnblockSource -> updatePreferences {
                it.copy(blockedSourceIds = it.blockedSourceIds - event.sourceId)
            }
            SettingsEvent.DismissError -> {
                failedUpdate = null
                edit { it.copy(updateFailed = false) }
            }
        }
    }

    private fun load() {
        _state.value = UiState.Loading
        viewModelScope.launch {
            val result = runCatching {
                coroutineScope {
                    val preferences = async { getPreferencesUseCase().getOrThrow() }
                    val options = async { getExploreFilterOptionsUseCase().getOrThrow() }
                    val sources = async { getFeedSourcesUseCase().getOrThrow() }
                    Triple(
                        first = preferences.await(),
                        second = options.await(),
                        third = sources.await(),
                    )
                }
            }
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { (preferences, options, sources) ->
                    sourceCatalog = sources.associateBy { it.id }
                    availableLanguages = options.languages
                    failedUpdate = null
                    _state.value = UiState.Success(
                        data = SettingsUiModel().withPreferences(preferences = preferences),
                    )
                },
                onFailure = { exception ->
                    _state.value = UiState.Error(message = exception.message.orEmpty())
                },
            )
        }
    }

    private fun edit(transform: (SettingsUiModel) -> SettingsUiModel) {
        _state.update { state ->
            val current = (state as? UiState.Success)?.data ?: return@update state
            UiState.Success(data = transform(current))
        }
    }

    private fun updatePreferences(transform: (UserPreferences) -> UserPreferences) {
        val current = (_state.value as? UiState.Success)?.data ?: return
        if (current.isUpdating) return
        val next = normalize(preferences = transform(current.preferences))
        if (next == current.preferences) return
        failedUpdate = null
        _state.value = UiState.Success(
            data = current.copy(
                isUpdating = true,
                updateFailed = false,
            ).withPreferences(preferences = next),
        )
        viewModelScope.launch {
            val result = updatePreferencesUseCase(transform = transform)
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { saved ->
                    edit {
                        it.copy(isUpdating = false).withPreferences(preferences = saved)
                    }
                },
                onFailure = {
                    failedUpdate = transform
                    edit {
                        it.copy(
                            isUpdating = false,
                            updateFailed = true,
                        ).withPreferences(preferences = current.preferences)
                    }
                },
            )
        }
    }

    private fun SettingsUiModel.withPreferences(preferences: UserPreferences): SettingsUiModel {
        val normalized = normalize(preferences)
        return copy(
            preferences = normalized,
            languageOptions = languageOptions(
                values = availableLanguages,
                selected = normalized.languages,
            ),
            selectedLanguageCodes = normalized.languages,
            mutedCategories = normalized.mutedCategories,
            mutedKeywords = normalized.mutedKeywords,
            blockedSources = normalized.blockedSourceIds.map { id ->
                sourceCatalog[id] ?: Source(
                    id = id,
                    url = "",
                    title = "",
                )
            },
        )
    }
}

fun languageOptions(
    values: List<String>,
    selected: Set<String>,
): List<LanguageOption> {
    val isoCodes = Locale.getISOLanguages().toSet()
    val available = values.map { it.trim().lowercase(Locale.ROOT) }.filter { it in isoCodes }
    val retained = selected.map { it.trim().lowercase(Locale.ROOT) }.filter(String::isNotBlank)
    return (available + retained)
        .distinct()
        .map { code ->
            LanguageOption(
                code = code,
                displayName = if (code in isoCodes) {
                    Locale.forLanguageTag(code).getDisplayLanguage(Locale.getDefault())
                } else {
                    code.uppercase(Locale.ROOT)
                },
            )
        }
        .sortedWith(
            comparator = compareBy<LanguageOption> { it.displayName.lowercase(Locale.ROOT) }
                .thenBy { it.code },
        )
}

private fun normalize(preferences: UserPreferences) = preferences.copy(
    mutedKeywords = clean(values = preferences.mutedKeywords),
    mutedCategories = clean(values = preferences.mutedCategories),
    languages = clean(values = preferences.languages.toList()).map {
        it.lowercase(Locale.ROOT)
    }.toSet(),
)

private fun clean(values: List<String>) = values
    .map(String::trim)
    .filter(String::isNotBlank)
    .distinctBy { it.lowercase(Locale.ROOT) }
