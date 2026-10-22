package com.srnyndrs.android.briefly.ui.screen.auth.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthFormState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.preview.AuthPreviewData
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun AuthFormContainer(
    modifier: Modifier = Modifier,
    form: AuthFormState,
    enabled: Boolean,
    title: String,
    submitLabel: String,
    navigationLabel: String,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onNavigation: () -> Unit,
) {

    var passwordVisible by rememberSaveable { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current

    Column(
        modifier = Modifier.then(modifier)
            .fillMaxWidth()
            .padding(
                horizontal = 12.dp,
                vertical = 12.dp,
            ),
        verticalArrangement = Arrangement.spacedBy(18.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onPrimaryContainer,
            textAlign = TextAlign.Center,
        )
        EmailTextField(
            modifier = Modifier.fillMaxWidth(),
            value = form.email,
            onValueChange = onEmailChange,
            enabled = enabled,
            error = if (form.emailRequired) stringResource(R.string.auth_email_required) else null,
            onNext = { focusManager.moveFocus(focusDirection = FocusDirection.Down) },
        )
        PasswordTextField(
            modifier = Modifier.fillMaxWidth(),
            value = form.password,
            onValueChange = onPasswordChange,
            passwordVisible = passwordVisible,
            onPasswordVisibilityChange = { passwordVisible = it },
            enabled = enabled,
            error = if (form.passwordRequired) stringResource(R.string.auth_password_required) else null,
            onSubmit = {
                focusManager.clearFocus()
                onSubmit()
            },
        )
        Button(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp),
            enabled = enabled,
            shape = RoundedCornerShape(5.dp),
            onClick = {
                focusManager.clearFocus()
                onSubmit()
            },
        ) {
            Text(text = submitLabel)
        }
        TextButton(
            enabled = enabled,
            onClick = onNavigation,
        ) {
            Text(
                text = navigationLabel,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@PreviewLightDark
@Composable
private fun AuthFormContainerPreview() {
    BrieflyTheme {
        Surface {
            AuthFormContainer(
                form = AuthPreviewData.form,
                enabled = true,
                title = stringResource(R.string.auth_login_title),
                submitLabel = stringResource(R.string.auth_login),
                navigationLabel = stringResource(R.string.auth_go_to_register),
                onEmailChange = {},
                onPasswordChange = {},
                onSubmit = {},
                onNavigation = {},
            )
        }
    }
}
