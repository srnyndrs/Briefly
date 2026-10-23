package com.srnyndrs.android.briefly.ui.screen.auth.screen

import com.srnyndrs.android.briefly.ui.model.UiState

data class AuthFormState(
    val email: String = "",
    val password: String = "",
    val validationRequested: Boolean = false,
) {
    val emailRequired: Boolean get() = validationRequested && email.isBlank()
    val passwordRequired: Boolean get() = validationRequested && password.isEmpty()
}

data class AuthScreenState(
    val isRegistering: Boolean = false,
    val login: AuthFormState = AuthFormState(),
    val registration: AuthFormState = AuthFormState(),
    val submission: UiState<Unit> = UiState.Idle,
) {
    val form: AuthFormState get() = if (isRegistering) registration else login
}
