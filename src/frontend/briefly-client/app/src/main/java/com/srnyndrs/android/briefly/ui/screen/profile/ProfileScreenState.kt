package com.srnyndrs.android.briefly.ui.screen.profile

import com.srnyndrs.android.briefly.domain.model.profile.ProfileData

data class ProfileScreenState (
    val email: String = "",
    val selectedLanguages: Set<String> = emptySet(),
    val mutedKeywords: List<String> = emptyList(),
)

fun ProfileData.toProfileScreenState(): ProfileScreenState {
    return ProfileScreenState(
        email = this.email,
        selectedLanguages = this.preferences.languages,
        mutedKeywords = this.preferences.mutedKeywords
    )
}
