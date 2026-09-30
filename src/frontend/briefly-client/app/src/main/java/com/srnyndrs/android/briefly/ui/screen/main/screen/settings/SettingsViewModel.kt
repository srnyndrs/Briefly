package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.GetFeedSourcesUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetPreferenceOptionsUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetProfileUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.UpdatePreferencesUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import java.util.Locale
import javax.inject.Inject
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val getProfileUseCase: GetProfileUseCase,
    private val getPreferenceOptionsUseCase: GetPreferenceOptionsUseCase,
    private val getFeedSourcesUseCase: GetFeedSourcesUseCase,
    private val updatePreferencesUseCase: UpdatePreferencesUseCase,
) : ViewModel() {

    private val _state = MutableStateFlow<UiState<SettingsUiModel>>(UiState.Idle)
    val state = _state.asStateFlow()

    init { load() }

    fun onEvent(event: SettingsEvent) {
        when (event) {
            SettingsEvent.RetryLoad -> {
                load()
            }
            is SettingsEvent.ToggleLanguage -> {
                updatePreferences { it.copy(languages = toggle(it.languages, event.code)) }
            }
            is SettingsEvent.RemoveMutedCategory -> {
                updatePreferences { it.copy(mutedCategories = it.mutedCategories.filterNot { value -> value.equals(event.category, true) }) }
            }
            is SettingsEvent.KeywordDraftChanged -> {
                edit { it.copy(keywordDraft = event.value) }
            }
            SettingsEvent.AddMutedKeyword -> {
                val model = (_state.value as? UiState.Success)?.data ?: return
                val keyword = model.keywordDraft.trim()
                if (keyword.isNotBlank() && model.mutedKeywords.none { it.equals(keyword, true) }) {
                    updatePreferences { it.copy(mutedKeywords = it.mutedKeywords + keyword) }
                }
            }
            is SettingsEvent.RemoveMutedKeyword -> {
                updatePreferences { it.copy(mutedKeywords = it.mutedKeywords.filterNot { value -> value.equals(event.keyword, true) }) }
            }
            is SettingsEvent.UnblockSource -> {
                updatePreferences { it.copy(blockedSourceIds = it.blockedSourceIds - event.sourceId) }
            }
            SettingsEvent.DismissError -> {
                edit { it.copy(errorMessage = null) }
            }
        }
    }

    private fun load() = viewModelScope.launch {
        _state.value = UiState.Loading
        runCatching { coroutineScope {
                Triple(
                    async { getProfileUseCase().getOrThrow() },
                    async { getPreferenceOptionsUseCase().getOrThrow() },
                    async { getFeedSourcesUseCase().getOrThrow() }
                ).let {
                    Triple(
                        it.first.await(),
                        it.second.await(),
                        it.third.await()
                    )
                }
            }
        }.fold(
            onSuccess = { (profile, options, sources) ->
                _state.value = UiState.Success(normalize(profile.preferences)
                    .toUiModel(options.languages, sources)
                )},
            onFailure = {
                _state.value = UiState.Error(it.message ?: "Unable to load preferences")
            }
        )
    }

    private fun edit(transform: (SettingsUiModel) -> SettingsUiModel) {
        val current = (_state.value as? UiState.Success)?.data ?: return
        _state.value = UiState.Success(transform(current))
    }

    private fun updatePreferences(transform: (ProfilePreferences) -> ProfilePreferences) {
        val current = (_state.value as? UiState.Success)?.data ?: return
        if (current.isUpdating) return
        val previous = current.preferences
        val next = normalize(transform(previous))
        if (next == previous) return
        _state.value = UiState.Success(current.copy(preferences = next, isUpdating = true, errorMessage = null).withPreferences(next))
        viewModelScope.launch {
            updatePreferencesUseCase(next).fold(
                onSuccess = { saved ->
                    edit { it.copy(
                        preferences = normalize(saved),
                        isUpdating = false
                    ).withPreferences(normalize(saved)) } },
                onFailure = { error ->
                    edit { it.copy(
                        preferences = previous,
                        isUpdating = false,
                        errorMessage = error.message ?: "Unable to update settings"
                    ).withPreferences(previous) }
                },
            )
        }
    }

    private fun SettingsUiModel.withPreferences(preferences: ProfilePreferences) = copy(
        selectedLanguageCodes = preferences.languages,
        mutedCategories = preferences.mutedCategories,
        mutedKeywords = preferences.mutedKeywords,
        blockedSources = blockedSources.filter {
            it.id in preferences.blockedSourceIds
        }
    )

    private fun toggle(values: Set<String>, value: String): Set<String> =
        values.firstOrNull { it.equals(value, true) }?.let { values - it } ?: (values + value)
}

private fun ProfilePreferences.toUiModel(languages: List<String>, sources: List<Source>): SettingsUiModel {
    val normalized = normalize(this)
    val merged = sources + normalized.blockedSourceIds.filterNot { id -> sources.any { it.id == id } }.map { Source(it, "", "Unavailable source") }
    return SettingsUiModel(languageOptions = languageOptions(languages, normalized.languages), selectedLanguageCodes = normalized.languages, mutedCategories = normalized.mutedCategories, mutedKeywords = normalized.mutedKeywords, blockedSources = merged.filter { it.id in normalized.blockedSourceIds }, preferences = normalized)
}

fun languageOptions(values: List<String>, selected: Set<String>): List<LanguageOption> = (values + selected).map { it.trim().lowercase(Locale.ROOT) }.filter { it.length == 2 && it.all(Char::isLetter) }.distinct().map { code -> LanguageOption(code, Locale.forLanguageTag(code).getDisplayLanguage(Locale.getDefault()).ifBlank { code.uppercase(Locale.ROOT) }) }.sortedWith(compareBy<LanguageOption> { it.displayName.lowercase(Locale.ROOT) }.thenBy { it.code })
private fun normalize(p: ProfilePreferences) = p.copy(mutedKeywords = clean(p.mutedKeywords), mutedCategories = clean(p.mutedCategories), languages = clean(p.languages).map { it.lowercase(Locale.ROOT) }.toSet())
private fun clean(values: List<String>) = values.map(String::trim).filter(String::isNotBlank).distinctBy { it.lowercase(Locale.ROOT) }
private fun clean(values: Set<String>) = clean(values.toList()).toSet()
