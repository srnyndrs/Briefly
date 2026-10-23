package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.LanguageOption
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.preview.SettingsPreviewData
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import java.util.Locale

@Composable
fun LanguageSelectionList(
    modifier: Modifier = Modifier,
    options: List<LanguageOption>,
    selectedCodes: Set<String>,
    enabled: Boolean,
    onToggle: (String) -> Unit,
) {
    Column(modifier = modifier) {
        options.forEach { option ->
            val selected = option.code in selectedCodes
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 48.dp)
                    .toggleable(
                        value = selected,
                        enabled = enabled,
                        role = Role.Checkbox,
                        onValueChange = { onToggle(option.code) },
                    )
                    .padding(vertical = 4.dp),
            ) {
                Checkbox(
                    checked = selected,
                    onCheckedChange = null,
                    enabled = enabled,
                )
                Column(modifier = Modifier.padding(start = 8.dp)) {
                    Text(text = option.displayName)
                    Text(
                        text = option.code.uppercase(Locale.ROOT),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
        if (selectedCodes.isEmpty()) {
            Text(
                text = stringResource(id = R.string.settings_no_language_filter),
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@PreviewLightDark
@Composable
fun LanguageSelectionListPreview() {
    BrieflyTheme {
        Surface {
            LanguageSelectionList(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(all = 12.dp),
                options = SettingsPreviewData.model.languageOptions,
                selectedCodes = SettingsPreviewData.model.selectedLanguageCodes,
                enabled = true,
                onToggle = {},
            )
        }
    }
}
