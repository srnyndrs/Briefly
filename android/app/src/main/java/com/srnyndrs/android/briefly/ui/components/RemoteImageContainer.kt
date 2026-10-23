package com.srnyndrs.android.briefly.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImagePainter
import coil3.compose.rememberAsyncImagePainter
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun RemoteImageContainer(
    modifier: Modifier = Modifier,
    imageUrl: String,
    contentDescription: String?,
    contentScale: ContentScale = ContentScale.Crop,
    enableFade: Boolean = false,
) {

    val painter = rememberAsyncImagePainter(model = imageUrl)
    val state by painter.state.collectAsStateWithLifecycle()

    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.Center,
    ) {
        RemoteImage(
            modifier = Modifier.fillMaxSize(),
            painter = painter,
            state = state,
            contentDescription = contentDescription,
            contentScale = contentScale,
        )
        if (enableFade && state is AsyncImagePainter.State.Success) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.125f)),
            )
        }
    }
}

@PreviewLightDark
@Composable
private fun RemoteImageContainerPreview() {
    BrieflyTheme {
        Surface {
            RemoteImageContainer(
                modifier = Modifier.size(
                    width = 128.dp,
                    height = 72.dp,
                ),
                imageUrl = "",
                contentDescription = null,
            )
        }
    }
}
