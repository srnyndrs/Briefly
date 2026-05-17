package com.srnyndrs.android.briefly.data.remote.di

import com.srnyndrs.android.briefly.data.local.auth.TokenManager
import com.srnyndrs.android.briefly.data.remote.auth.AuthApiService
import com.srnyndrs.android.briefly.data.remote.auth.dto.RefreshRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.TokenPairDto
import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.repository.auth.AuthRepositoryImpl
import com.srnyndrs.android.briefly.data.repository.content.ContentRepositoryImpl
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.auth.Auth
import io.ktor.client.plugins.auth.providers.BearerTokens
import io.ktor.client.plugins.auth.providers.bearer
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.plugins.logging.LogLevel
import io.ktor.client.plugins.logging.Logger
import io.ktor.client.plugins.logging.Logging
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideKtorClient(tokenManager: TokenManager): HttpClient = HttpClient(OkHttp) {
        expectSuccess = true
        install(Logging) {
            level = LogLevel.INFO
            logger = object : Logger {
                override fun log(message: String) {
                    println("Ktor: $message")
                }
            }
        }
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                prettyPrint = true
                isLenient = true
            })
        }
        install(Auth) {
            bearer {
                loadTokens {
                    val accessToken = tokenManager.getAccessToken()
                    val refreshToken = tokenManager.getRefreshToken()
                    if (accessToken != null && refreshToken != null) {
                        BearerTokens(accessToken, refreshToken)
                    } else {
                        null
                    }
                }
                refreshTokens {
                    val refreshToken = tokenManager.getRefreshToken() ?: return@refreshTokens null
                    try {
                        val response = client.post("auth/refresh") {
                            markAsRefreshTokenRequest()
                            setBody(RefreshRequestDto(refreshToken))
                        }.body<TokenPairDto>()
                        
                        tokenManager.saveAccessToken(response.accessToken)
                        tokenManager.saveRefreshToken(response.refreshToken)
                        BearerTokens(response.accessToken, response.refreshToken)
                    } catch (_: Exception) {
                        tokenManager.clearTokens()
                        null
                    }
                }
            }
        }
        defaultRequest {
            // TODO: use BuildConfig
            url("http://10.0.2.2:8000/")
            contentType(ContentType.Application.Json)
        }
    }

    @Provides
    @Singleton
    fun provideAuthApiService(client: HttpClient): AuthApiService = AuthApiService(client)

    @Provides
    @Singleton
    fun provideAuthRepository(
        authApiService: AuthApiService,
        tokenManager: TokenManager
    ): AuthRepository {
        return AuthRepositoryImpl(authApiService, tokenManager)
    }

    @Provides
    @Singleton
    fun provideContentApiService(client: HttpClient): ContentApiService = ContentApiService(client)

    @Provides
    @Singleton
    fun provideContentRepository(
        contentApiService: ContentApiService
    ): ContentRepository {
        return ContentRepositoryImpl(contentApiService)
    }

}
