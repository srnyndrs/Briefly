package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.ui.screen.main.components.preview.PostPreviewProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlin.time.ExperimentalTime

@Composable
fun PostRow(
    modifier: Modifier = Modifier,
    title: String,
    source: String?,
    onClick: () -> Unit,
) {
    Column(
        modifier = Modifier
            .then(modifier)
            .background(color = MaterialTheme.colorScheme.surface)
            .clickable(
                role = Role.Button,
                onClick = onClick,
            ),
        verticalArrangement = Arrangement.spacedBy(space = 12.dp),
    ) {
        source?.takeIf { it.isNotBlank() }?.let { sourceTitle ->
            Text(
                text = sourceTitle,
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = title,
            minLines = 1,
            maxLines = 3,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Black,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun PostRowPreview(
    @PreviewParameter(PostPreviewProvider::class) post: Post,
) {
    BrieflyTheme {
        Surface {
            PostRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(all = 6.dp),
                title = post.title,
                source = post.sourceTitle,
                onClick = {},
            )
        }
    }
}
