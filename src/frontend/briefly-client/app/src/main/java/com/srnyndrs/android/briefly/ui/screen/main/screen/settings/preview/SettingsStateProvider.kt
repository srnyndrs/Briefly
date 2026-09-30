package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.LanguageOption
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.SettingsUiModel

object SettingsPreviewData {
    private val preferences = UserPreferences(
        mutedKeywords = listOf("batteries", "recycling"),
        mutedCategories = listOf("technology", "health"),
        blockedSourceIds = setOf("source", "unavailable"),
        languages = setOf("en", "pt-br"),
    )
    val model = SettingsUiModel(
        languageOptions = listOf(
            LanguageOption(
                code = "en",
                displayName = "English",
            ),
            LanguageOption(
                code = "hu",
                displayName = "Hungarian",
            ),
            LanguageOption(
                code = "pt-br",
                displayName = "PT-BR",
            ),
        ),
        selectedLanguageCodes = preferences.languages,
        mutedCategories = preferences.mutedCategories,
        mutedKeywords = preferences.mutedKeywords,
        keywordDraft = "research",
        blockedSources = listOf(
            Source(
                id = "source",
                url = "https://example.com/rss",
                title = "Example News",
            ),
            Source(
                id = "unavailable",
                url = "",
                title = "",
            ),
        ),
        preferences = preferences,
    )
}

class SettingsStateProvider : PreviewParameterProvider<UiState<SettingsUiModel>> {
    override val values = sequenceOf(
        UiState.Loading,
        UiState.Error(message = "Preview failure"),
        UiState.Success(data = SettingsPreviewData.model),
        UiState.Success(data = SettingsPreviewData.model.copy(isUpdating = true)),
        UiState.Success(data = SettingsPreviewData.model.copy(updateFailed = true)),
    )
}
