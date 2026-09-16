package com.srnyndrs.android.briefly.data.repository.auth

import com.srnyndrs.android.briefly.data.local.auth.AuthSessionManager
import com.srnyndrs.android.briefly.data.remote.auth.AuthApiService
import com.srnyndrs.android.briefly.data.remote.auth.dto.LoginRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.LogoutRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.RefreshRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.RegisterRequestDto
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import io.ktor.client.plugins.ClientRequestException
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject

class AuthRepositoryImpl @Inject constructor(
    private val apiAuthService: AuthApiService,
    private val authSessionManager: AuthSessionManager,
) : AuthRepository {

    override suspend fun login(
        email: String,
        password: String
    ): Result<Unit> {
        return try {
            val response = apiAuthService.login(LoginRequestDto(email, password))
            authSessionManager.saveTokens(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
            )
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun register(
        email: String,
        password: String
    ): Result<Unit> {
        return try {
            val response = apiAuthService.register(RegisterRequestDto(email, password))
            authSessionManager.saveTokens(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
            )
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun refreshSession(): Result<Unit> {
        val refreshToken = authSessionManager.getRefreshToken()
        if (refreshToken == null) {
            authSessionManager.invalidate()
            return Result.failure(IllegalStateException("No refresh token"))
        }

        authSessionManager.setLoading()
        return try {
            val response = apiAuthService.refresh(RefreshRequestDto(refreshToken))
            authSessionManager.saveTokens(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
            )
            Result.success(Unit)
        } catch (exception: ClientRequestException) {
            if (exception.response.status == HttpStatusCode.Unauthorized) {
                authSessionManager.invalidate()
            } else {
                authSessionManager.markUnavailable()
            }
            Result.failure(exception)
        } catch (exception: Exception) {
            authSessionManager.markUnavailable()
            Result.failure(exception)
        }
    }

    override suspend fun logout(): Result<Unit> {
        return try {
            val refreshToken = authSessionManager.getRefreshToken()
            if (refreshToken != null) {
                apiAuthService.logout(LogoutRequestDto(refreshToken))
            }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        } finally {
            authSessionManager.invalidate()
        }
    }

    override fun observeAuthState(): StateFlow<AuthState> = authSessionManager.authState
}
