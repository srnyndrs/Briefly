package com.srnyndrs.android.briefly.data.repository.profile

import com.srnyndrs.android.briefly.data.remote.profile.ProfileApiService
import com.srnyndrs.android.briefly.data.remote.profile.toDomain
import com.srnyndrs.android.briefly.data.remote.profile.toPatchDto
import com.srnyndrs.android.briefly.domain.model.profile.ProfileData
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import javax.inject.Inject

class ProfileRepositoryImpl @Inject constructor(
    private val profileApi: ProfileApiService,
): ProfileRepository {

    override suspend fun getProfile(): Result<ProfileData> {
        return try {
            val response = profileApi.getProfile()

            Result.success(response.toDomain())
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun updatePreferences(preferences: ProfilePreferences): Result<ProfilePreferences> {
        return try {
            val response = profileApi.updatePreferences(preferences.toPatchDto())
            Result.success(response.toDomain())
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

}
