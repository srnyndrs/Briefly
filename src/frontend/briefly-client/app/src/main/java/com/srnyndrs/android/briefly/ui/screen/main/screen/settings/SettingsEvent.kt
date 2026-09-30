package com.srnyndrs.android.briefly.ui.screen.main.screen.settings

sealed interface SettingsEvent {
    data object RetryLoad : SettingsEvent
    data class ToggleLanguage(val code: String) : SettingsEvent
    data class RemoveMutedCategory(val category: String) : SettingsEvent
    data class KeywordDraftChanged(val value: String) : SettingsEvent
    data object AddMutedKeyword : SettingsEvent
    data class RemoveMutedKeyword(val keyword: String) : SettingsEvent
    data class UnblockSource(val sourceId: String) : SettingsEvent
    data object DismissError : SettingsEvent
}
