package com.srnyndrs.android.briefly.data.repository.auth

import com.srnyndrs.android.briefly.data.local.auth.TokenManager
import com.srnyndrs.android.briefly.data.remote.auth.AuthApiService
import com.srnyndrs.android.briefly.data.remote.auth.dto.LoginRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.LogoutRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.RegisterRequestDto
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject

class AuthRepositoryImpl @Inject constructor(
    private val apiAuthService: AuthApiService,
    private val tokenManager: TokenManager
): AuthRepository {

    private val _authState = MutableStateFlow(
        if (tokenManager.getRefreshToken() != null) AuthState.Authenticated else AuthState.Unauthenticated
    )

    override suspend fun login(
        email: String,
        password: String
    ): Result<Unit> {
        _authState.value = AuthState.Loading
        return try {
            val response = apiAuthService.login(LoginRequestDto(email, password))
            tokenManager.saveAccessToken(response.accessToken)
            tokenManager.saveRefreshToken(response.refreshToken)
            _authState.value = AuthState.Authenticated
            Result.success(Unit)
        } catch (e: Exception) {
            _authState.value = AuthState.Unauthenticated
            Result.failure(e)
        }
    }

    override suspend fun register(
        email: String,
        password: String
    ): Result<Unit> {
        _authState.value = AuthState.Loading
        return try {
            val response = apiAuthService.register(RegisterRequestDto(email, password))
            tokenManager.saveAccessToken(response.accessToken)
            tokenManager.saveRefreshToken(response.refreshToken)
            _authState.value = AuthState.Authenticated
            Result.success(Unit)
        } catch (e: Exception) {
            _authState.value = AuthState.Unauthenticated
            Result.failure(e)
        }
    }

    override suspend fun refreshSession(): Result<Unit> {
        // Handled automatically by Ktor Auth plugin.
        // We could manually trigger a protected endpoint or just verify token existence.
        val hasRefreshToken = tokenManager.getRefreshToken() != null
        _authState.value = if (hasRefreshToken) AuthState.Authenticated else AuthState.Unauthenticated
        return if (hasRefreshToken) Result.success(Unit) else Result.failure(Exception("No refresh token"))
    }

    override suspend fun logout(): Result<Unit> {
        return try {
            val refreshToken = tokenManager.getRefreshToken()
            if (refreshToken != null) {
                apiAuthService.logout(LogoutRequestDto(refreshToken))
            }
            tokenManager.clearTokens()
            _authState.value = AuthState.Unauthenticated
            Result.success(Unit)
        } catch (e: Exception) {
            tokenManager.clearTokens()
            _authState.value = AuthState.Unauthenticated
            Result.failure(e)
        }
    }

    override fun observeAuthState(): Flow<AuthState> {
        return _authState.asStateFlow()
    }
}
