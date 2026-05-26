package com.srnyndrs.android.briefly.ui.screen.auth.screen

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.auth.AllAuthUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val allAuthUseCase: AllAuthUseCase
): ViewModel() {

    private val _state = MutableStateFlow<UiState<Unit>>(UiState.Idle)
    val state = _state.asStateFlow()

    init {
        autoLogin()
    }

    fun onEvent(event: AuthEvent) {
        when(event) {
            is AuthEvent.LoginWithEmail -> {
                val (email, password) = event
                loginWithEmail(email, password)
            }
            is AuthEvent.RegisterWithEmail -> {
                val (username, email, password) = event
                registerWithEmail(username, email, password)
            }
        }
    }

    private fun loginWithEmail(email: String, password: String) = viewModelScope.launch {
        _state.value = UiState.Loading
        allAuthUseCase.loginUseCase(email, password).fold(
            onSuccess = {
                _state.value = UiState.Success(data = Unit)
            },
            onFailure = { error ->
                _state.value = UiState.Error(message = error.message ?: "Unexpected error occurred")
            }
        )
    }

    private fun registerWithEmail(username: String, email: String, password: String) = viewModelScope.launch {
        _state.value = UiState.Loading
        allAuthUseCase.registerUseCase(username, email, password).fold(
            onSuccess = {
                _state.value = UiState.Success(data = Unit)
            },
            onFailure = { error ->
                _state.value = UiState.Error(message = error.message ?: "Unexpected error occurred")
            }
        )
    }

    private fun autoLogin() = viewModelScope.launch {
        allAuthUseCase.refreshSessionUseCase().fold(
            onSuccess = {
                _state.value = UiState.Success(data = Unit)
            },
            onFailure = {
                _state.value = UiState.Idle
            }
        )
    }

}
