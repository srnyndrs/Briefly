package com.srnyndrs.android.briefly.domain.usecase.preferences

import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import javax.inject.Inject

class SetSourceBlockedUseCase @Inject constructor(
    private val updatePreferencesUseCase: UpdatePreferencesUseCase,
) {
    suspend operator fun invoke(
        sourceId: String,
        blocked: Boolean,
    ): Result<UserPreferences> = updatePreferencesUseCase { preferences ->
        val blockedSourceIds = if (blocked) {
            preferences.blockedSourceIds + sourceId
        } else {
            preferences.blockedSourceIds - sourceId
        }
        preferences.copy(blockedSourceIds = blockedSourceIds)
    }
}
