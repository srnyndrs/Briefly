package com.srnyndrs.android.briefly.data.repository.auth

import com.srnyndrs.android.briefly.data.local.auth.AuthSessionManager
import com.srnyndrs.android.briefly.data.remote.auth.AuthApiService
import com.srnyndrs.android.briefly.data.remote.auth.LoginRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.LogoutRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.RefreshRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.RegisterRequestDto
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import io.ktor.client.plugins.ClientRequestException
import io.ktor.http.HttpStatusCode
import javax.inject.Inject
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.StateFlow

class AuthRepositoryImpl @Inject constructor(
    private val apiAuthService: AuthApiService,
    private val authSessionManager: AuthSessionManager,
) : AuthRepository {

    override fun observeAuthState(): StateFlow<AuthState> = authSessionManager.authState

    override suspend fun login(
        email: String,
        password: String,
    ): Result<Unit> {
        return try {
            val response = apiAuthService.login(
                request = LoginRequestDto(
                    email = email,
                    password = password,
                )
            )
            currentCoroutineContext().ensureActive()
            authSessionManager.saveTokens(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
            )
            Result.success(value = Unit)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun register(
        email: String,
        password: String,
    ): Result<Unit> {
        return try {
            val response = apiAuthService.register(
                request = RegisterRequestDto(
                    email = email,
                    password = password,
                )
            )
            currentCoroutineContext().ensureActive()
            authSessionManager.saveTokens(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
            )
            Result.success(value = Unit)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun refreshSession(): Result<Unit> {
        val refreshToken = authSessionManager.getRefreshToken()
        if (refreshToken == null) {
            authSessionManager.invalidateTokens()
            return Result.failure(
                exception = IllegalStateException("No refresh token")
            )
        }

        authSessionManager.setLoading()

        return try {
            val response = apiAuthService.refresh(
                request = RefreshRequestDto(refreshToken = refreshToken)
            )
            currentCoroutineContext().ensureActive()
            authSessionManager.saveTokens(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
            )
            Result.success(value = Unit)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: ClientRequestException) {
            if (exception.response.status == HttpStatusCode.Unauthorized) {
                authSessionManager.invalidateTokens()
            } else {
                authSessionManager.markUnavailable()
            }
            Result.failure(exception = exception)
        } catch (exception: Exception) {
            authSessionManager.markUnavailable()
            Result.failure(exception = exception)
        }
    }

    override suspend fun logout(): Result<Unit> {
        return try {
            val refreshToken = authSessionManager.getRefreshToken()
            if (refreshToken != null) {
                apiAuthService.logout(
                    request = LogoutRequestDto(refreshToken = refreshToken)
                )
            }
            Result.success(value = Unit)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        } finally {
            authSessionManager.invalidateTokens()
        }
    }

}
