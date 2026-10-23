package com.srnyndrs.android.briefly.ui.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.repository.auth.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

@HiltViewModel
class AppViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {

    val authState = authRepository.observeAuthState()

    private var refreshJob: Job? = null

    init {
        refreshSession()
    }

    fun refreshSession() {
        if (refreshJob?.isActive == true) return
        refreshJob = viewModelScope.launch {
            authRepository.refreshSession()
        }
    }
}
