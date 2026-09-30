package com.srnyndrs.android.briefly.ui.screen.auth.screen

sealed interface AuthEvent {
    data class LoginWithEmail(val email: String, val password: String): AuthEvent
    data class RegisterWithEmail(val email: String, val password: String): AuthEvent
}
