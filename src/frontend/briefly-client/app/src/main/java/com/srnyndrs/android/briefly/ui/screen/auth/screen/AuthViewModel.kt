package com.srnyndrs.android.briefly.ui.screen.auth.screen

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.auth.AuthUseCases
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authUseCases: AuthUseCases,
) : ViewModel() {

    private val _state = MutableStateFlow(AuthScreenState())
    val state = _state.asStateFlow()

    fun onEvent(event: AuthEvent) {
        if (_state.value.submission is UiState.Loading || _state.value.submission is UiState.Success) return
        when (event) {
            is AuthEvent.UpdateEmailField -> updateForm { it.copy(email = event.email) }
            is AuthEvent.UpdatePasswordField -> updateForm { it.copy(password = event.password) }
            AuthEvent.NavigateLoginForm -> _state.update {
                it.copy(
                    isRegistering = false,
                    submission = UiState.Idle,
                )
            }
            AuthEvent.NavigateRegisterForm -> _state.update {
                it.copy(
                    isRegistering = true,
                    submission = UiState.Idle,
                )
            }
            AuthEvent.SubmitForm -> submit()
        }
    }

    private fun updateForm(transform: (AuthFormState) -> AuthFormState) {
        _state.update { current ->
            if (current.isRegistering) {
                current.copy(
                    registration = transform(current.registration),
                    submission = UiState.Idle,
                )
            } else {
                current.copy(
                    login = transform(current.login),
                    submission = UiState.Idle,
                )
            }
        }
    }

    private fun submit() {
        updateForm { it.copy(validationRequested = true) }
        val current = _state.value
        val form = current.form
        if (form.email.isBlank() || form.password.isEmpty()) return

        _state.value = current.copy(submission = UiState.Loading)
        viewModelScope.launch {
            val result = if (current.isRegistering) {
                authUseCases.registerUseCase(
                    email = form.email.trim(),
                    password = form.password,
                )
            } else {
                authUseCases.loginUseCase(
                    email = form.email.trim(),
                    password = form.password,
                )
            }
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = {
                    _state.update {
                        it.copy(
                            login = AuthFormState(),
                            registration = AuthFormState(),
                            submission = UiState.Success(data = Unit),
                        )
                    }
                },
                onFailure = { exception ->
                    _state.update {
                        it.copy(
                            submission = UiState.Error(
                                // TODO: localized fallback string
                                message = exception.localizedMessage ?: "Unexpected Error"
                            )
                        )
                    }
                },
            )
        }
    }
}
