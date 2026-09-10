package com.srnyndrs.android.briefly.ui.screen.profile

sealed class ProfileScreenEvent {
    data class UpdateLanguagePreferences(val languages: Set<String>): ProfileScreenEvent()
    data object Logout: ProfileScreenEvent()
}
