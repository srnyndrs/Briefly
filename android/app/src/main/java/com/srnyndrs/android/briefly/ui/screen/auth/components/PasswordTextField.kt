package com.srnyndrs.android.briefly.ui.screen.auth.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Eye
import com.composables.icons.heroicons.outline.EyeSlash
import com.composables.icons.heroicons.outline.LockClosed
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PasswordTextField(
    modifier: Modifier = Modifier,
    value: String,
    onValueChange: (String) -> Unit,
    passwordVisible: Boolean,
    onPasswordVisibilityChange: (Boolean) -> Unit,
    enabled: Boolean = true,
    error: String? = null,
    onSubmit: () -> Unit = {},
) {
    OutlinedTextField(
        modifier = Modifier.then(modifier),
        colors = AuthTextFieldColors,
        value = value,
        onValueChange = onValueChange,
        enabled = enabled,
        singleLine = true,
        isError = error != null,
        label = { Text(text = stringResource(R.string.auth_password)) },
        supportingText = error?.let { message -> { Text(text = message) } },
        leadingIcon = {
            Icon(
                imageVector = Heroicons.Outline.LockClosed,
                contentDescription = null,
            )
        },
        trailingIcon = {
            IconButton(
                enabled = enabled,
                onClick = { onPasswordVisibilityChange(!passwordVisible) },
            ) {
                Icon(
                    imageVector = if (passwordVisible) Heroicons.Outline.EyeSlash else Heroicons.Outline.Eye,
                    contentDescription = stringResource(
                        if (passwordVisible) R.string.auth_hide_password else R.string.auth_show_password,
                    ),
                )
            }
        },
        visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Done,
        ),
        keyboardActions = KeyboardActions(
            onDone = { if (enabled) onSubmit() }
        ),
    )
}

@PreviewLightDark
@Composable
private fun PasswordTextFieldPreview() {
    BrieflyTheme {
        Surface {
            PasswordTextField(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                value = "example-password",
                onValueChange = {},
                passwordVisible = false,
                onPasswordVisibilityChange = {},
            )
        }
    }
}
