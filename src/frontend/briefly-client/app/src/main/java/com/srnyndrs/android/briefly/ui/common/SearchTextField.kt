package com.srnyndrs.android.briefly.ui.common

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SearchTextField(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    placeholder: String = "Search",
    onSearch: (() -> Unit)? = null
) {
    OutlinedTextField(
        modifier = modifier.requiredHeight(52.dp),
        value = value,
        onValueChange = onValueChange,
        placeholder = { Text(placeholder) },
        singleLine = true,
        shape = RoundedCornerShape(5.dp),
        textStyle = MaterialTheme.typography.bodyMedium,
        trailingIcon = {
            IconButton(
                onClick = { onSearch?.invoke() }
            ) {
                Icon(
                    imageVector = Icons.Default.Search,
                    contentDescription = null
                )
            }
        }
    )
}

@PreviewLightDark
@Composable
fun SearchTextFieldPreview() {
    BrieflyTheme {
        Surface {
            SearchTextField(
                modifier = Modifier.fillMaxWidth().padding(6.dp),
                value = "",
                onValueChange = {},
            ) {

            }
        }
    }
}
