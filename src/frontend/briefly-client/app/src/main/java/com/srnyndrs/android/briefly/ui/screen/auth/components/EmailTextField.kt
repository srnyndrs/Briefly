package com.srnyndrs.android.briefly.ui.screen.auth.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Envelope
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun EmailTextField(
    modifier: Modifier = Modifier,
    value: String,
    onValueChange: (String) -> Unit,
    enabled: Boolean = true,
    error: String? = null,
    onNext: () -> Unit = {},
) {
    OutlinedTextField(
        modifier = Modifier.then(modifier),
        colors = AuthTextFieldColors,
        value = value,
        onValueChange = onValueChange,
        enabled = enabled,
        singleLine = true,
        isError = error != null,
        label = { Text(text = stringResource(R.string.auth_email)) },
        supportingText = error?.let { message -> { Text(text = message) } },
        leadingIcon = {
            Icon(
                imageVector = Heroicons.Outline.Envelope,
                contentDescription = null,
            )
        },
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
        ),
        keyboardActions = KeyboardActions(onNext = { onNext() }),
    )
}

@PreviewLightDark
@Composable
private fun EmailTextFieldPreview() {
    BrieflyTheme {
        Surface {
            EmailTextField(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                value = "reader@example.com",
                onValueChange = {},
            )
        }
    }
}
