package com.srnyndrs.android.briefly.data.remote.profile

import com.srnyndrs.android.briefly.data.remote.profile.dto.PreferencesDto
import com.srnyndrs.android.briefly.data.remote.profile.dto.ProfileDataResponseDto
import com.srnyndrs.android.briefly.data.remote.profile.dto.PreferenceUpdateRequestDto
import com.srnyndrs.android.briefly.domain.model.profile.ProfileData
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences

fun ProfileDataResponseDto.toDomain(): ProfileData {
    return ProfileData(
        email = this.email,
        preferences = this.preferences.toDomain()
    )
}

fun PreferencesDto.toDomain(): ProfilePreferences {
    return ProfilePreferences(
        mutedKeywords = this.mutedKeywords,
        mutedCategories = this.mutedCategories,
        blockedSourceIds = this.blockedSourceIds.toSet(),
        languages = this.languages.toSet(),
    )
}

fun ProfilePreferences.toPatchDto(): PreferenceUpdateRequestDto {
    return PreferenceUpdateRequestDto(
        mutedKeywords = mutedKeywords,
        mutedCategories = mutedCategories,
        blockedSourceIds = blockedSourceIds.toList(),
        languages = languages.toList(),
    )
}
