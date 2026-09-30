package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.*
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.LanguageOption
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun LanguageSelectionList(
    modifier: Modifier = Modifier,
    options: List<LanguageOption>,
    selectedCodes: Set<String>,
    enabled: Boolean,
    onToggle: (String) -> Unit)
{
    Column(
        modifier = Modifier.then(modifier)
    ) {
        options.forEach { option ->
            val selected = option.code in selectedCodes
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 48.dp)
                    .clickable(enabled) {
                        onToggle(option.code)
                    }
                    .semantics {
                        role = Role.Checkbox
                        this.selected = selected
                    }
                    .padding(vertical = 4.dp)
            ) {
                Checkbox(
                    checked = selected,
                    onCheckedChange = null,
                    enabled = enabled
                )
                Column(
                    modifier = Modifier.padding(start = 8.dp)
                ) {
                    Text(
                        text = option.displayName
                    )
                    Text(
                        text = option.code.uppercase(),
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
        if (selectedCodes.isEmpty()) {
            Text(
                text = "No language filter applied",
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

@PreviewLightDark
@Composable
fun LanguageSelectionListPreview() {
    BrieflyTheme {
        Surface {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                LanguageSelectionList(
                    modifier = Modifier.fillMaxWidth(),
                    options = listOf(
                        LanguageOption("hu", "Hungarian"),
                        LanguageOption("en", "English"),
                    ),
                    selectedCodes = setOf("hu"),
                    enabled = true,
                ) {}
            }
        }
    }
}
