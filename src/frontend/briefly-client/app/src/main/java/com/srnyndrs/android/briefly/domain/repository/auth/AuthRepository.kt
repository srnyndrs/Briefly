package com.srnyndrs.android.briefly.domain.repository.auth

import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    suspend fun login(email: String, password: String): Result<Unit>
    suspend fun register(email: String, password: String): Result<Unit>
    suspend fun refreshSession(): Result<Unit>
    suspend fun logout(): Result<Unit>
    fun observeAuthState(): Flow<AuthState>
}
