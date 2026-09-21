package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Surface
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.XMark
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PreferenceKeywordInput(
    modifier: Modifier = Modifier,
    value: String,
    keywords: List<String>,
    onValueChange: (String) -> Unit,
    onAdd: () -> Unit,
    onRemove: (String) -> Unit,
) {

    val removeDescription = stringResource(R.string.settings_remove_keyword)

    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        OutlinedTextField(
            modifier = Modifier.weight(1f),
            value = value,
            onValueChange = onValueChange,
            label = {
                Text(
                    text = stringResource(R.string.settings_muted_placeholder)
                )
            },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(onDone = { onAdd() }),
        )
        AssistChip(
            onClick = onAdd,
            label = {
                Text(
                    text = stringResource(R.string.settings_add_keyword)
                )
            },
        )
    }
    FlowRow(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        keywords.forEach { keyword ->
            AssistChip(
                onClick = { onRemove(keyword) },
                label = { Text(text = keyword) },
                trailingIcon = {
                    Icon(
                        imageVector = Heroicons.Solid.XMark,
                        contentDescription = stringResource(R.string.settings_remove_keyword),
                    )
                },
                modifier = Modifier.semantics {
                    contentDescription = "$keyword: $removeDescription"
                },
            )
        }
    }
}

@PreviewLightDark
@Composable
fun PreferenceKeywordInputPreview() {
    BrieflyTheme {
        Surface {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                PreferenceKeywordInput(
                    modifier = Modifier.fillMaxWidth(),
                    value = "",
                    keywords = listOf("Donald", "Trump"),
                    onValueChange = {},
                    onAdd = {},
                ) {}
            }
        }
    }
}
