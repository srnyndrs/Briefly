package com.srnyndrs.android.briefly.domain.repository.profile

import com.srnyndrs.android.briefly.domain.model.profile.ProfileData
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences

interface ProfileRepository {
    suspend fun getProfile(): Result<ProfileData>
    suspend fun updatePreferences(preferences: ProfilePreferences): Result<ProfilePreferences>
}
