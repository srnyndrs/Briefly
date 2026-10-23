package com.srnyndrs.android.briefly.ui.screen.auth.screen

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Newspaper
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.login.LoginScreen
import com.srnyndrs.android.briefly.ui.screen.auth.screen.preview.AuthScreenStateProvider
import com.srnyndrs.android.briefly.ui.screen.auth.screen.register.RegisterScreen
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun AuthScreen(
    modifier: Modifier = Modifier,
    state: AuthScreenState,
    onAuthEvent: (AuthEvent) -> Unit,
) {

    val enabled = state.submission !is UiState.Loading && state.submission !is UiState.Success

    Scaffold(
        modifier = Modifier.then(modifier)
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .imePadding(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            UiStateContainer(
                modifier = Modifier
                    .fillMaxWidth()
                    .semantics { liveRegion = LiveRegionMode.Polite },
                state = state.submission,
                loading = {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        CircularProgressIndicator(modifier = Modifier.size(24.dp))
                        Text(
                            text = stringResource(
                                if (state.isRegistering) R.string.auth_registering else R.string.auth_submitting,
                            ),
                        )
                    }
                },
                error = {
                    Text(
                        modifier = Modifier.padding(16.dp),
                        text = stringResource(
                            if (state.isRegistering) R.string.auth_register_error else R.string.auth_submit_error,
                        ),
                        color = MaterialTheme.colorScheme.error,
                    )
                },
                success = {},
            )
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 12.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(20.dp),
                ) {
                    Icon(
                        modifier = Modifier.size(52.dp),
                        imageVector = Heroicons.Outline.Newspaper,
                        tint = MaterialTheme.colorScheme.onPrimaryContainer,
                        contentDescription = null,
                    )
                    Text(
                        text = stringResource(R.string.app_name),
                        style = MaterialTheme.typography.headlineLarge,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
                HorizontalDivider()
                if (state.isRegistering) {
                    RegisterScreen(
                        modifier = Modifier.fillMaxWidth(),
                        form = state.registration,
                        enabled = enabled,
                        onEmailChange = { onAuthEvent(AuthEvent.UpdateEmailField(email = it)) },
                        onPasswordChange = { onAuthEvent(AuthEvent.UpdatePasswordField(password = it)) },
                        onNavigation = { onAuthEvent(AuthEvent.NavigateLoginForm) },
                        onRegister = { onAuthEvent(AuthEvent.SubmitForm) },
                    )
                } else {
                    LoginScreen(
                        modifier = Modifier.fillMaxWidth(),
                        form = state.login,
                        enabled = enabled,
                        onEmailChange = { onAuthEvent(AuthEvent.UpdateEmailField(email = it)) },
                        onPasswordChange = { onAuthEvent(AuthEvent.UpdatePasswordField(password = it)) },
                        onNavigation = { onAuthEvent(AuthEvent.NavigateRegisterForm) },
                        onLogin = { onAuthEvent(AuthEvent.SubmitForm) },
                    )
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun AuthScreenPreview(
    @PreviewParameter(AuthScreenStateProvider::class) state: AuthScreenState,
) {
    BrieflyTheme {
        Surface {
            AuthScreen(
                modifier = Modifier.fillMaxSize(),
                state = state,
                onAuthEvent = {},
            )
        }
    }
}
