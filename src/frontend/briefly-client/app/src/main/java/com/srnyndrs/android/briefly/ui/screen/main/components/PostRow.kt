package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PostRow(
    modifier: Modifier = Modifier,
    title: String,
    source: String?,
    onClick: () -> Unit,
) {
    Column(
        modifier = Modifier.then(modifier)
            .background(MaterialTheme.colorScheme.surface)
            .clickable {
                onClick()
            },
            //.padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Source
        source?.let { sourceTitle ->
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                // Source name
                Text(
                    text = sourceTitle,
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }
        }
        // Title
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = title,
            minLines = 1,
            maxLines = 3,
            textAlign = TextAlign.Start,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Black,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@PreviewLightDark
@Composable
fun PostRowPreview() {
    BrieflyTheme {
        Surface {
            Column (
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(6.dp)
            ) {
                PostRow(
                    modifier = Modifier.fillMaxWidth(),
                    title = "Új programmal fogja támogatni az EU a hadiipari újítások átültetését a gyakorlatba",
                    source = "Telex"
                ) { }
                HorizontalDivider()
            }
        }
    }
}
