package com.srnyndrs.android.briefly.ui.common

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.srnyndrs.android.briefly.ui.model.UiState

@Composable
fun <T> UiStateContainer(
    modifier: Modifier = Modifier,
    state: UiState<T>,
    content: @Composable (data: T?, isLoading: Boolean) -> Unit
) {
    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.Center
    ) {
        when(state) {
            is UiState.Idle -> {}
            is UiState.Error -> {
                Text(
                    modifier = Modifier.fillMaxWidth(),
                    text = state.message,
                    color = MaterialTheme.colorScheme.error
                )
            }
            else -> {
                val data = (state as? UiState.Success)?.data
                val isLoading = state == UiState.Loading

                content(data, isLoading)
            }
        }
    }
}
