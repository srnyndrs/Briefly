package com.srnyndrs.android.briefly.domain.repository.profile

import com.srnyndrs.android.briefly.domain.model.profile.ProfileData

interface ProfileRepository {
    suspend fun getProfile(): Result<ProfileData>
}
