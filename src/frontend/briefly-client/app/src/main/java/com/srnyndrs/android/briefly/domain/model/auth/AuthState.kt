package com.srnyndrs.android.briefly.domain.model.auth

sealed interface AuthState {
    data object Loading : AuthState
    data object Authenticated : AuthState
    data object Unauthenticated : AuthState
}
