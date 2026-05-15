package com.srnyndrs.android.briefly.domain.usecase.auth

import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import javax.inject.Inject

class RefreshSessionUseCase @Inject constructor(
    private val repository: AuthRepository
) {
    suspend operator fun invoke(): Result<Unit> = repository.refreshSession()
}
