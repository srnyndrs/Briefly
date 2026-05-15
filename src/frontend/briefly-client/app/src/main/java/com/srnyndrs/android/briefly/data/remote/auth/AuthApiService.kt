package com.srnyndrs.android.briefly.data.remote.auth

import com.srnyndrs.android.briefly.data.remote.auth.dto.LoginRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.LogoutRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.RegisterRequestDto
import com.srnyndrs.android.briefly.data.remote.auth.dto.TokenPairDto
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.post
import io.ktor.client.request.setBody

class AuthApiService(
    private val client: HttpClient
) {

    suspend fun login(request: LoginRequestDto): TokenPairDto {
        return client.post("auth/login") {
            setBody(request)
        }.body()
    }

    suspend fun register(request: RegisterRequestDto): TokenPairDto {
        return client.post("auth/register") {
            setBody(request)
        }.body()
    }

    suspend fun logout(request: LogoutRequestDto) {
        client.post("auth/logout") {
            setBody(request)
        }
    }
}
