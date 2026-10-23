package com.srnyndrs.android.briefly.data.di

import com.srnyndrs.android.briefly.BuildConfig
import com.srnyndrs.android.briefly.data.local.auth.AuthSessionManager
import com.srnyndrs.android.briefly.data.remote.auth.AuthApiService
import com.srnyndrs.android.briefly.data.remote.auth.RefreshRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.TokenPairResponseDto
import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.source.SourceApiService
import com.srnyndrs.android.briefly.data.remote.profile.ProfileApiService
import com.srnyndrs.android.briefly.data.repository.auth.AuthRepositoryImpl
import com.srnyndrs.android.briefly.data.repository.content.ContentRepositoryImpl
import com.srnyndrs.android.briefly.data.repository.content.source.SourceRepositoryImpl
import com.srnyndrs.android.briefly.data.repository.profile.ProfileRepositoryImpl
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import com.srnyndrs.android.briefly.domain.repository.profile.ProfileRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.ClientRequestException
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
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import javax.inject.Singleton
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.serialization.json.Json

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private const val TOKEN_REFRESH_PATH = "auth/refresh"

    @Provides
    @Singleton
    fun provideKtorClient(
        authSessionManager: AuthSessionManager,
    ): HttpClient = HttpClient(OkHttp) {
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
                    val accessToken = authSessionManager.getAccessToken()
                    val refreshToken = authSessionManager.getRefreshToken()
                    if (accessToken != null && refreshToken != null) {
                        BearerTokens(accessToken, refreshToken)
                    } else {
                        null
                    }
                }
                refreshTokens {
                    val refreshToken = authSessionManager.getRefreshToken()
                        ?: return@refreshTokens null
                    try {
                        val response = client.post(TOKEN_REFRESH_PATH) {
                            markAsRefreshTokenRequest()
                            setBody(RefreshRequestDto(refreshToken))
                        }.body<TokenPairResponseDto>()

                        currentCoroutineContext().ensureActive()
                        authSessionManager.saveTokens(
                            accessToken = response.accessToken,
                            refreshToken = response.refreshToken,
                        )
                        BearerTokens(response.accessToken, response.refreshToken)
                    } catch (exception: CancellationException) {
                        throw exception
                    } catch (exception: ClientRequestException) {
                        if (exception.response.status == HttpStatusCode.Unauthorized) {
                            authSessionManager.invalidateTokens()
                        }
                        null
                    } catch (_: Exception) {
                        null
                    }
                }
            }
        }
        defaultRequest {
            url(BuildConfig.BACKEND_BASE_URL)
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
        authSessionManager: AuthSessionManager,
    ): AuthRepository {
        return AuthRepositoryImpl(authApiService, authSessionManager)
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

    @Provides
    @Singleton
    fun provideSourceApiService(client: HttpClient): SourceApiService = SourceApiService(client)

    @Provides
    @Singleton
    fun provideSourceRepository(
        sourceApiService: SourceApiService
    ): SourceRepository {
        return SourceRepositoryImpl(sourceApiService)
    }

    @Provides
    @Singleton
    fun provideProfileApiService(client: HttpClient): ProfileApiService = ProfileApiService(client)

    @Provides
    @Singleton
    fun provideProfileRepository(
        profileApiService: ProfileApiService
    ): ProfileRepository {
        return ProfileRepositoryImpl(profileApiService)
    }

}
