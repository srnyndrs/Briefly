package com.srnyndrs.android.briefly.ui.screen.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.auth.LogoutUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class MainViewModel @Inject constructor(
    private val logoutUseCase: LogoutUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(MainState())
    val state = _state.asStateFlow()

    fun onEvent(event: MainEvent) {
        when (event) {
            MainEvent.SignOut -> {
                if (_state.value.isSigningOut) return
                _state.value = MainState(isSigningOut = true)
                viewModelScope.launch {
                    try {
                        logoutUseCase()
                    } finally {
                        _state.value = MainState()
                    }
                }
            }
        }
    }
}
