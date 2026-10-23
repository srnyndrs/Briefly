package com.srnyndrs.android.briefly.domain.usecase.auth

import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import javax.inject.Inject

class LogoutUseCase @Inject constructor(
    private val repository: AuthRepository
) {
    suspend operator fun invoke() = repository.logout()
}
