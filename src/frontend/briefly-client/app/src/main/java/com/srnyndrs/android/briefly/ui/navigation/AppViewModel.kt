package com.srnyndrs.android.briefly.ui.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AppViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {

    val authState = authRepository.observeAuthState()

    init {
        refreshSession()
    }

    fun refreshSession() = viewModelScope.launch {
        authRepository.refreshSession()
    }
}
