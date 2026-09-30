package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

@Composable
fun PostRow(
    modifier: Modifier = Modifier,
    title: String,
    source: String?,
    onClick: () -> Unit,
) {
    Column(
        modifier = modifier
            .clickable {
                onClick()
            },
        verticalArrangement = Arrangement.spacedBy(8.dp)
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
