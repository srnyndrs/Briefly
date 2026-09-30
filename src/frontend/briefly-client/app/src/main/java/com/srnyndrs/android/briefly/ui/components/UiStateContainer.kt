package com.srnyndrs.android.briefly.ui.components

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

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
        modifier = Modifier.then(modifier),
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

@PreviewLightDark
@Composable
fun UiStateContainerPreview() {
    BrieflyTheme {
        Surface {
            
            val state by remember { mutableStateOf(UiState.Success("Success")) }
            
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                UiStateContainer(
                    modifier = Modifier.fillMaxWidth(),
                    state = state,
                    idle = {},
                    loading = {},
                    error = {},
                ) { data ->
                    Text(
                        text = data,
                        style = MaterialTheme.typography.titleLarge
                    )
                }
            }
        }
    }
}
