package com.srnyndrs.android.briefly.domain.usecase.preferences

import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import javax.inject.Inject

class MuteKeywordUseCase @Inject constructor(
    private val updatePreferencesUseCase: UpdatePreferencesUseCase,
) {
    suspend operator fun invoke(keyword: String): Result<UserPreferences> = updatePreferencesUseCase { preferences ->
        val trimmedKeyword = keyword.trim()
        val alreadyMuted = preferences.mutedKeywords.any {
            it.equals(
                other = trimmedKeyword,
                ignoreCase = true,
            )
        }
        if (trimmedKeyword.isEmpty() || alreadyMuted) {
            preferences
        } else {
            preferences.copy(mutedKeywords = preferences.mutedKeywords + trimmedKeyword)
        }
    }
}
