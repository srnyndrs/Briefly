package com.srnyndrs.android.briefly.ui.screen.profile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.auth.LogoutUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetProfileUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val logoutUseCase: LogoutUseCase,
    private val getProfileUseCase: GetProfileUseCase
): ViewModel() {

    private val _state = MutableStateFlow<UiState<ProfileScreenState>>(UiState.Idle)
    val state = _state.asStateFlow()
        .onStart { getProfileData() }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000L),
            UiState.Idle
        )

    private fun getProfileData() = viewModelScope.launch {
        _state.value = UiState.Loading

        getProfileUseCase().fold(
            onSuccess = { data ->
                _state.value = UiState.Success(data = data.toProfileScreenState())
            },
            onFailure = { exception ->
                _state.value = UiState.Error(message = exception.message ?: "An error occurred")
            }
        )
    }

    fun onEvent(event: ProfileScreenEvent) = viewModelScope.launch {
        when(event) {
            ProfileScreenEvent.Logout -> {
                logoutUseCase().fold(
                    onSuccess = {
                        // TODO
                    },
                    onFailure = {
                        // TODO
                    }
                )
            }
            is ProfileScreenEvent.UpdateLanguagePreferences -> {
                // TODO
            }
        }
    }

}
