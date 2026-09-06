package com.srnyndrs.android.briefly.domain.usecase.auth

import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import javax.inject.Inject

class RegisterUseCase @Inject constructor(
    private val repository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): Result<Unit> =
        repository.register(email, password)
}
