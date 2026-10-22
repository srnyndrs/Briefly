package com.srnyndrs.android.briefly.domain.repository.profile

import com.srnyndrs.android.briefly.domain.model.profile.Profile
import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences

interface ProfileRepository {
    suspend fun getProfile(): Result<Profile>
    suspend fun getPreferences(): Result<UserPreferences>
    suspend fun updatePreferences(preferences: UserPreferences): Result<UserPreferences>
}
