package com.srnyndrs.android.briefly.ui.screen.auth.components

import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.KeyboardArrowDown
import androidx.compose.material.icons.outlined.KeyboardArrowUp
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.graphics.vector.rememberVectorPainter
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PasswordTextField(
    modifier: Modifier = Modifier,
    value: String,
    onValueChange: (String) -> Unit,
    label: String = "Password",
    leadingIcon: Painter? = rememberVectorPainter(image = Icons.Outlined.Lock),
    passwordVisible: Boolean,
    onPasswordVisibilityChange: (Boolean) -> Unit,
) {
    val interactionSource: MutableInteractionSource = remember { MutableInteractionSource() }
    val textFieldIsFocused = interactionSource.collectIsFocusedAsState()

    val actualVisualTransformation = if (passwordVisible) {
        VisualTransformation.None
    } else {
        PasswordVisualTransformation()
    }

    val trailingIcon = rememberVectorPainter(
        image = if (passwordVisible) Icons.Outlined.KeyboardArrowDown else Icons.Outlined.KeyboardArrowUp
    )

    OutlinedTextField(
        modifier = Modifier.then(modifier),
        colors = AuthTextFieldColors,
        value = value,
        onValueChange = onValueChange,
        label = {
            val style =
                if (textFieldIsFocused.value) MaterialTheme.typography.titleSmall
                else MaterialTheme.typography.bodyMedium

            Text(text = label, style = style)
        },
        leadingIcon = leadingIcon?.let {
            @Composable {
                Icon(
                    modifier = Modifier.size(28.dp),
                    painter = leadingIcon, contentDescription = null
                )
            }
        },
        trailingIcon = {
            IconButton(onClick = { onPasswordVisibilityChange(!passwordVisible) }) {
                Icon(
                    modifier = Modifier.size(28.dp),
                    painter = trailingIcon, contentDescription = null
                )
            }
        },
        interactionSource = interactionSource,
        visualTransformation = actualVisualTransformation,
        keyboardOptions = KeyboardOptions.Default.copy(
            keyboardType = KeyboardType.Password
        )
    )
}

@PreviewLightDark
@Composable
private fun PasswordTextFieldPreview() {
    BrieflyTheme {
        var password by remember { mutableStateOf("") }
        var passwordVisible by remember { mutableStateOf(false) }

        Surface(
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth().padding(12.dp)
            ) {
                PasswordTextField(
                    modifier = Modifier
                        .fillMaxWidth(),
                    value = password,
                    onValueChange = {
                        password = it
                    },
                    passwordVisible = passwordVisible,
                    onPasswordVisibilityChange = { passwordVisible = it }
                )
            }
        }
    }
}
