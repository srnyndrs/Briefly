package com.srnyndrs.android.briefly.domain.usecase.profile

import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import javax.inject.Inject

class SetSourceBlockedUseCase @Inject constructor(
    private val repository: ProfileRepository,
) {
    suspend operator fun invoke(
        sourceId: String,
        blocked: Boolean,
    ): Result<ProfilePreferences> {
        val preferences = repository.getProfile().getOrElse { return Result.failure(it) }.preferences
        val blockedSourceIds = if (blocked) {
            preferences.blockedSourceIds + sourceId
        } else {
            preferences.blockedSourceIds - sourceId
        }
        if (blockedSourceIds == preferences.blockedSourceIds) return Result.success(preferences)
        return repository.updatePreferences(
            preferences = preferences.copy(blockedSourceIds = blockedSourceIds),
        )
    }
}
