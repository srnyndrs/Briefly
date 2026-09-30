package com.srnyndrs.android.briefly.data.repository.profile

import com.srnyndrs.android.briefly.data.remote.profile.ProfileApiService
import com.srnyndrs.android.briefly.data.remote.profile.toDomain
import com.srnyndrs.android.briefly.data.remote.profile.toPatchDto
import com.srnyndrs.android.briefly.domain.model.profile.Profile
import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import javax.inject.Inject
import kotlinx.coroutines.CancellationException

class ProfileRepositoryImpl @Inject constructor(
    private val profileApi: ProfileApiService,
): ProfileRepository {

    override suspend fun getProfile(): Result<Profile> {
        return try {
            val response = profileApi.getProfile()

            Result.success(response.toDomain())
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun getPreferences(): Result<UserPreferences> {
        return try {
            val response = profileApi.getPreferences()
            Result.success(value = response.toDomain())
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun updatePreferences(preferences: UserPreferences): Result<UserPreferences> {
        return try {
            val response = profileApi.updatePreferences(preferences.toPatchDto())
            Result.success(response.toDomain())
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

}
