package com.srnyndrs.android.briefly.data.remote.profile

import com.srnyndrs.android.briefly.domain.model.profile.Profile
import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences

fun ProfileDataResponseDto.toDomain(): Profile {
    return Profile(
        email = this.email,
        preferences = preferences?.toDomain() ?: UserPreferences(
            mutedKeywords = emptyList(),
            mutedCategories = emptyList(),
            blockedSourceIds = emptySet(),
            languages = emptySet(),
        ),
    )
}

fun PreferencesDto.toDomain(): UserPreferences {
    return UserPreferences(
        mutedKeywords = this.mutedKeywords,
        mutedCategories = this.mutedCategories,
        blockedSourceIds = this.blockedSourceIds.toSet(),
        languages = this.languages.toSet(),
    )
}

fun UserPreferences.toPatchDto(): PreferenceUpdateRequestDto {
    return PreferenceUpdateRequestDto(
        mutedKeywords = mutedKeywords,
        mutedCategories = mutedCategories,
        blockedSourceIds = blockedSourceIds.toList(), // TODO: revisit base type if it could be a Set
        languages = languages.toList(), // TODO: revisit base type if it could be a Set
    )
}
