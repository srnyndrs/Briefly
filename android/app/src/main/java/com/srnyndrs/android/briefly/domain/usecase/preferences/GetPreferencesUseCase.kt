package com.srnyndrs.android.briefly.domain.usecase.preferences

import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import javax.inject.Inject

class GetPreferencesUseCase @Inject constructor(
    private val repository: ProfileRepository,
) {
    suspend operator fun invoke(): Result<UserPreferences> {
        return repository.getPreferences()
    }
}
