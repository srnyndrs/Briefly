package com.srnyndrs.android.briefly.ui.screen.content.screen

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.auth.LogoutUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ContentViewModel @Inject constructor(
    private val logoutUseCase: LogoutUseCase
): ViewModel() {

    fun logoutUser(onSuccess: () -> Unit = {}) = viewModelScope.launch {
        logoutUseCase().fold(
            onSuccess = {
                onSuccess()
            },
            onFailure = {
                onSuccess()
            }
        )
    }
}
