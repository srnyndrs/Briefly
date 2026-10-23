package com.srnyndrs.android.briefly.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.painter.ColorPainter
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImagePainter
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ExclamationTriangle
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun RemoteImage(
    modifier: Modifier = Modifier,
    painter: Painter,
    state: AsyncImagePainter.State,
    contentDescription: String?,
    contentScale: ContentScale = ContentScale.Crop,
) {
    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.Center,
    ) {
        when (state) {
            is AsyncImagePainter.State.Empty,
            is AsyncImagePainter.State.Loading -> {
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(color = MaterialTheme.colorScheme.surface.copy(alpha = 0.6f)),
                    isLoading = true,
                ) {}
            }
            is AsyncImagePainter.State.Success -> {
                Image(
                    modifier = Modifier.fillMaxSize(),
                    contentScale = contentScale,
                    painter = painter,
                    contentDescription = contentDescription,
                )
            }
            is AsyncImagePainter.State.Error -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(color = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.6f)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        modifier = Modifier.size(size = 24.dp),
                        imageVector = Heroicons.Outline.ExclamationTriangle,
                        contentDescription = if (contentDescription != null) {
                            stringResource(
                                R.string.image_unavailable,
                                contentDescription,
                            )
                        } else {
                            null
                        },
                        tint = MaterialTheme.colorScheme.onErrorContainer.copy(alpha = 0.7f),
                    )
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
private fun RemoteImagePreview() {
    val painter = ColorPainter(color = Color.Gray)
    val request = ImageRequest.Builder(context = LocalContext.current).build()
    val states = listOf(
        AsyncImagePainter.State.Loading(painter = null),
        AsyncImagePainter.State.Error(
            painter = null,
            result = ErrorResult(
                image = null,
                request = request,
                throwable = IllegalStateException(),
            ),
        ),
    )
    BrieflyTheme {
        Surface {
            Column(verticalArrangement = Arrangement.spacedBy(space = 12.dp)) {
                states.forEach { state ->
                    RemoteImage(
                        modifier = Modifier.size(
                            width = 128.dp,
                            height = 72.dp,
                        ),
                        painter = painter,
                        state = state,
                        contentDescription = "Article illustration",
                    )
                }
            }
        }
    }
}
