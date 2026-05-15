package com.srnyndrs.android.briefly.ui.screen.auth.screen

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.login.LoginScreen
import com.srnyndrs.android.briefly.ui.screen.auth.screen.register.RegisterScreen
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AuthScreen(
    modifier: Modifier = Modifier,
    state: UiState<Unit> = UiState.Idle,
    onSuccess: () -> Unit,
    onEvent: (AuthEvent) -> Unit
) {

    val scope = rememberCoroutineScope()
    val pagerState = rememberPagerState { 2 }
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state) {
        when (state) {
            is UiState.Success -> onSuccess()
            is UiState.Error -> snackbarHostState.showSnackbar(
                message = state.message,
                withDismissAction = true,
                duration = SnackbarDuration.Short
            )
            else -> Unit
        }
    }

    Scaffold(
        modifier = modifier,
        snackbarHost = {
            SnackbarHost(hostState = snackbarHostState)
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(256.dp),
                    verticalArrangement = Arrangement.Center
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(
                                color = MaterialTheme.colorScheme.onSurface.copy(0.2f)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Image(
                            painter = painterResource(R.drawable.ic_launcher_foreground),
                            contentDescription = null // TODO
                        )
                    }
                }
                HorizontalPager(
                    modifier = Modifier.fillMaxWidth(),
                    state = pagerState,
                    userScrollEnabled = false
                ) { page ->
                    when (page) {
                        0 -> {
                            LoginScreen(
                                modifier = Modifier.fillMaxSize(),
                                onNavigation = {
                                    scope.launch {
                                        pagerState.animateScrollToPage(1)
                                    }
                                }
                            ) { email, password ->
                                onEvent(AuthEvent.LoginWithEmail(email, password))
                            }
                        }
                        1 -> {
                            RegisterScreen(
                                modifier = Modifier.fillMaxSize(),
                                onNavigation = {
                                    scope.launch {
                                        pagerState.animateScrollToPage(0)
                                    }
                                }
                            ) { email, password ->
                                onEvent(AuthEvent.RegisterWithEmail(email, password))
                            }
                        }
                    }
                }
            }

            if (state is UiState.Loading) {
                LoadingOverlay()
            }
        }
    }
}

@Composable
private fun LoadingOverlay() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.6f)),
        contentAlignment = Alignment.Center
    ) {
        CircularProgressIndicator()
    }
}

@PreviewLightDark
@Composable
fun AuthScreenPreview() {
    BrieflyTheme {
        Surface {
            AuthScreen(
                modifier = Modifier.fillMaxSize(),
                state = UiState.Idle,
                onSuccess = {}
            ) {

            }
        }
    }
}
