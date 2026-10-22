package com.srnyndrs.android.briefly.ui.screen.auth.screen.register

import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.screen.auth.components.AuthFormContainer
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthFormState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.preview.AuthFormStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun RegisterScreen(
    modifier: Modifier = Modifier,
    form: AuthFormState,
    enabled: Boolean,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onNavigation: () -> Unit,
    onRegister: () -> Unit,
) {
    AuthFormContainer(
        modifier = Modifier.then(modifier),
        form = form,
        enabled = enabled,
        title = stringResource(R.string.auth_register_title),
        submitLabel = stringResource(R.string.auth_register),
        navigationLabel = stringResource(R.string.auth_go_to_login),
        onEmailChange = onEmailChange,
        onPasswordChange = onPasswordChange,
        onSubmit = onRegister,
        onNavigation = onNavigation,
    )
}

@PreviewLightDark
@Composable
fun RegisterScreenPreview(
    @PreviewParameter(AuthFormStateProvider::class) form: AuthFormState,
) {
    BrieflyTheme {
        Surface {
            RegisterScreen(
                form = form,
                enabled = true,
                onEmailChange = {},
                onPasswordChange = {},
                onNavigation = {},
                onRegister = {},
            )
        }
    }
}
