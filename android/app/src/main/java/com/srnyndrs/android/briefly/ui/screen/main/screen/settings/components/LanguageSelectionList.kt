package com.srnyndrs.android.briefly.ui.screen.main.screen.settings.components

import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.ui.Alignment
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
                verticalAlignment = Alignment.CenterVertically
            ) {
                Checkbox(
                    checked = selected,
                    onCheckedChange = null,
                    enabled = enabled,
                )
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(3.dp)
                ) {
                    val (code, displayName) = option
                    Text(
                        text = displayName
                    )
                    Text(
                        text = "(${code.uppercase(Locale.ROOT)})",
                    )
                }
            }
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
