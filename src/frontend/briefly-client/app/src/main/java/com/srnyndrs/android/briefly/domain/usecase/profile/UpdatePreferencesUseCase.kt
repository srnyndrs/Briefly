package com.srnyndrs.android.briefly.domain.usecase.profile

import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import javax.inject.Inject

class UpdatePreferencesUseCase @Inject constructor(
    private val repository: ProfileRepository,
) {
    suspend operator fun invoke(preferences: ProfilePreferences): Result<ProfilePreferences> {
        return repository.updatePreferences(preferences)
    }
}
