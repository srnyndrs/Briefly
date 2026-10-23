package com.srnyndrs.android.briefly.domain.usecase.preferences

import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

@Singleton
class UpdatePreferencesUseCase @Inject constructor(
    private val repository: ProfileRepository,
) {
    private val mutex = Mutex()

    suspend operator fun invoke(
        transform: (UserPreferences) -> UserPreferences,
    ): Result<UserPreferences> = mutex.withLock {
        val current = repository.getPreferences().getOrElse {
            return@withLock Result.failure(exception = it)
        }
        val updated = transform(current)
        if (updated == current) return@withLock Result.success(value = current)
        repository.updatePreferences(preferences = updated)
    }
}
