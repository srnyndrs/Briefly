package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences

data class LanguageOption(
    val code: String,
    val displayName: String
)

data class SettingsUiModel(
    val languageOptions: List<LanguageOption> = emptyList(),
    val selectedLanguageCodes: Set<String> = emptySet(),
    val mutedCategories: List<String> = emptyList(),
    val mutedKeywords: List<String> = emptyList(),
    val keywordDraft: String = "",
    val blockedSources: List<Source> = emptyList(),
    val preferences: ProfilePreferences = ProfilePreferences(
        mutedKeywords = emptyList(),
        mutedCategories = emptyList(),
        blockedSourceIds = emptySet(),
        languages = emptySet()
    ),
    val isUpdating: Boolean = false,
    val errorMessage: String? = null,
)
