package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
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
    enabled: Boolean,
    onValueChange: (String) -> Unit,
    onAdd: () -> Unit,
    onRemove: (String) -> Unit,
) {
    val canAdd = enabled && value.isNotBlank()
    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
        ) {
            OutlinedTextField(
                modifier = Modifier.weight(weight = 1f),
                value = value,
                onValueChange = onValueChange,
                enabled = enabled,
                label = { Text(text = stringResource(id = R.string.settings_muted_placeholder)) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = { if (canAdd) onAdd() }),
            )
            AssistChip(
                enabled = canAdd,
                onClick = onAdd,
                label = { Text(text = stringResource(id = R.string.settings_add_keyword)) },
            )
        }
        FlowRow(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(space = 8.dp),
            verticalArrangement = Arrangement.spacedBy(space = 4.dp),
        ) {
            keywords.forEach { keyword ->
                val removeDescription = stringResource(
                    id = R.string.settings_unmute_keyword,
                    keyword,
                )
                AssistChip(
                    modifier = Modifier.semantics { contentDescription = removeDescription },
                    enabled = enabled,
                    onClick = { onRemove(keyword) },
                    label = { Text(text = keyword) },
                    trailingIcon = {
                        Icon(
                            imageVector = Heroicons.Solid.XMark,
                            contentDescription = null,
                        )
                    },
                )
            }
        }
    }
}

@PreviewLightDark
@Composable
fun PreferenceKeywordInputPreview() {
    BrieflyTheme {
        Surface {
            PreferenceKeywordInput(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(all = 12.dp),
                value = "research",
                keywords = listOf("batteries", "recycling"),
                enabled = true,
                onValueChange = {},
                onAdd = {},
                onRemove = {},
            )
        }
    }
}
