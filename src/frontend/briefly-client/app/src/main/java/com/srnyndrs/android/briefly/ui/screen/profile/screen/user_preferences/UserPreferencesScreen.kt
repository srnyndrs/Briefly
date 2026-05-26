package com.srnyndrs.android.briefly.ui.screen.profile.screen.user_preferences

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun UserPreferencesScreen(
    modifier: Modifier = Modifier
) {

    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = "Preferences",
            textAlign = TextAlign.Center,
            style = MaterialTheme.typography.headlineSmall,
        )
    }
}

@PreviewLightDark
@Composable
fun UserPreferencesScreenPreview() {
    BrieflyTheme {
        Surface {
            UserPreferencesScreen(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(6.dp)
            )
        }
    }
}
