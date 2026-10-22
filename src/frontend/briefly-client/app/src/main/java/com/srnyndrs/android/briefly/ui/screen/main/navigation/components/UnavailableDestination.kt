package com.srnyndrs.android.briefly.ui.screen.main.navigation.components

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun UnavailableDestination(
    modifier: Modifier = Modifier,
    message: String,
    onBack: () -> Unit,
) {
    BackHandler(onBack = onBack)
    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier
                .verticalScroll(state = rememberScrollState())
                .padding(all = 24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(space = 16.dp),
        ) {
            Text(
                text = message,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center,
            )
            Button(onClick = onBack) {
                Text(text = stringResource(id = R.string.navigate_back))
            }
        }
    }
}

@PreviewLightDark
@Composable
private fun UnavailableDestinationPreview() {
    BrieflyTheme {
        Surface {
            UnavailableDestination(
                modifier = Modifier.fillMaxSize(),
                message = stringResource(id = R.string.navigation_article_unavailable),
                onBack = {},
            )
        }
    }
}
