package com.srnyndrs.android.briefly.data.remote.auth.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequestDto(
    val email: String,
    val password: String,
)

@Serializable
data class RegisterRequestDto(
    val email: String,
    val password: String,
)

@Serializable
data class RefreshRequestDto(
    @SerialName("refresh_token")
    val refreshToken: String,
)

@Serializable
data class LogoutRequestDto(
    @SerialName("refresh_token")
    val refreshToken: String,
    val reason: String = "logout",
)

@Serializable
data class TokenPairDto(
    @SerialName("access_token")
    val accessToken: String,
    @SerialName("refresh_token")
    val refreshToken: String,
)
