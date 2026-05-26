package com.srnyndrs.android.briefly.ui.screen.auth.components

import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Icon
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
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Envelope
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun EmailTextField(
    modifier: Modifier = Modifier,
    value: String,
    onValueChange: (String) -> Unit,
    label: String = "Email",
    leadingIcon: Painter? = rememberVectorPainter(image = Heroicons.Outline.Envelope),
) {

    val interactionSource: MutableInteractionSource = remember { MutableInteractionSource() }
    val textFieldIsFocused = interactionSource.collectIsFocusedAsState()

    OutlinedTextField(
        modifier = Modifier.then(modifier),
        colors = AuthTextFieldColors,
        value = value,
        onValueChange = onValueChange,
        label = {
            val style =
                if (textFieldIsFocused.value) MaterialTheme.typography.titleSmall
                else MaterialTheme.typography.bodyMedium

            Text(
                text = label,
                style = style
            )
        },
        leadingIcon = leadingIcon?.let {
            @Composable {
                Icon(
                    modifier = Modifier.size(24.dp),
                    painter = leadingIcon,
                    contentDescription = null
                )
            }
        },
        interactionSource = interactionSource,
        keyboardOptions = KeyboardOptions.Default.copy(
            keyboardType = KeyboardType.Email
        )
    )
}

@PreviewLightDark
@Composable
private fun EmailTextFieldPreview() {
    BrieflyTheme {
        var email by remember { mutableStateOf("") }

        Surface(
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth().padding(12.dp)
            ) {
                EmailTextField(
                    modifier = Modifier
                        .fillMaxWidth(),
                    value = email,
                    onValueChange = {
                        email = it
                    }
                )
            }
        }
    }
}
