package com.srnyndrs.android.briefly.ui.screen.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ProfileScreen(
    modifier: Modifier = Modifier,
    state: UiState<ProfileScreenState>
) {

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier.then(modifier)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        UiStateContainer(
            modifier = Modifier.fillMaxSize(),
            state = state
        ) { data, isLoading ->

        }
    }
}

@PreviewLightDark
@Composable
fun ProfileScreenPreview() {
    BrieflyTheme {
        Surface {
            ProfileScreen(
                modifier = Modifier.fillMaxSize(),
                state = UiState.Success(ProfileScreenState())
            )
        }
    }
}
