package com.srnyndrs.android.briefly.ui.screen.auth.screen

sealed interface AuthEvent {
    data class UpdateEmailField(val email: String): AuthEvent
    data class UpdatePasswordField(val password: String): AuthEvent
    data object NavigateLoginForm: AuthEvent
    data object NavigateRegisterForm: AuthEvent
    data object SubmitForm: AuthEvent
}
