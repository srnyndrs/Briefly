package com.srnyndrs.android.briefly.ui.components

import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.srnyndrs.android.briefly.ui.model.UiState

@Composable
fun <T : Any> UiStateContainer(
    modifier: Modifier = Modifier,
    state: UiState<T>,
    idle: @Composable () -> Unit = {},
    loading: @Composable () -> Unit,
    error: @Composable (message: String) -> Unit,
    success: @Composable (data: T) -> Unit,
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center,
    ) {
        when (state) {
            UiState.Idle -> idle()
            UiState.Loading -> loading()
            is UiState.Error -> error(state.message)
            is UiState.Success -> success(state.data)
        }
    }
}
