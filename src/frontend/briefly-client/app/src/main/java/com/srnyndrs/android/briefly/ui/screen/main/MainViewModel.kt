package com.srnyndrs.android.briefly.ui.screen.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import com.srnyndrs.android.briefly.domain.usecase.auth.LogoutUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MainViewModel @Inject constructor(
    private val logoutUseCase: LogoutUseCase
): ViewModel() {

    private val _logoutState = MutableStateFlow<AuthState>(AuthState.Authenticated)
    val logoutState = _logoutState.asStateFlow()

    fun logoutUser() = viewModelScope.launch {
        _logoutState.value = AuthState.Loading
        logoutUseCase().fold(
            onSuccess = {
                _logoutState.value = AuthState.Unauthenticated
            },
            onFailure = {
                _logoutState.value = AuthState.Authenticated
            }
        )
    }
}
