package com.srnyndrs.android.briefly.data.remote.auth

import com.srnyndrs.android.briefly.data.remote.auth.dto.LoginRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.LogoutRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.RefreshRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.RegisterRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.TokenPairResponseDto
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.post
import io.ktor.client.request.setBody

class AuthApiService(
    private val client: HttpClient
) {

    companion object {
        private const val BASE_AUTH_PATH = "auth"
    }

    suspend fun login(request: LoginRequestDto): TokenPairResponseDto {
        return client.post("${BASE_AUTH_PATH}/login") {
            setBody(request)
        }.body()
    }

    suspend fun register(request: RegisterRequestDto): TokenPairResponseDto {
        return client.post("${BASE_AUTH_PATH}/register") {
            setBody(request)
        }.body()
    }

    suspend fun refresh(request: RefreshRequestDto): TokenPairResponseDto {
        return client.post("${BASE_AUTH_PATH}/refresh") {
            setBody(request)
        }.body()
    }

    suspend fun logout(request: LogoutRequestDto) {
        client.post("${BASE_AUTH_PATH}/logout") {
            setBody(request)
        }
    }

}
