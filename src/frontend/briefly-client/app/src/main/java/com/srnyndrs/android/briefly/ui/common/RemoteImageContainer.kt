package com.srnyndrs.android.briefly.ui.common

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil3.compose.AsyncImagePainter
import coil3.compose.rememberAsyncImagePainter
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun RemoteImageContainer(
    modifier: Modifier = Modifier,
    imageUrl: String,
    contentScale: ContentScale = ContentScale.Crop
) {

    val painter = rememberAsyncImagePainter(imageUrl)
    val state by painter.state.collectAsState()

    Box(
        modifier = Modifier.then(modifier),
        contentAlignment = Alignment.Center
    ) {
        RemoteImage(
            painter = painter,
            state = state,
            contentScale = contentScale
        )
    }
}

@Composable
fun RemoteImage(
    painter: AsyncImagePainter,
    state: AsyncImagePainter.State,
    contentScale: ContentScale = ContentScale.Crop,
) {
    when (state) {
        is AsyncImagePainter.State.Empty,
        is AsyncImagePainter.State.Loading -> {
            CircularProgressIndicator()
        }
        is AsyncImagePainter.State.Success -> {
            Image(
                modifier = Modifier.fillMaxSize(),
                contentScale = contentScale,
                painter = painter,
                contentDescription = null // TODO
            )
        }
        is AsyncImagePainter.State.Error -> {
            // TODO: apply shimmer effect
            Box(
                modifier = Modifier.fillMaxSize()
                    .background(
                        MaterialTheme.colorScheme.errorContainer.copy(0.6f)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.Warning,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onErrorContainer.copy(0.4f),
                )
            }
        }
    }
}

@Preview
@Composable
fun RemoteImagePreview() {
    BrieflyTheme {
        Surface {

            val painter = rememberAsyncImagePainter("https://example.com/image.jpg")

            val stateList = listOf<AsyncImagePainter.State>(
                AsyncImagePainter.State.Error(
                    painter = painter,
                    ErrorResult(
                        image = null,
                        request = ImageRequest.Builder(
                            context = LocalContext.current
                        ).build(),
                        throwable = Exception(),
                    )
                ),
                AsyncImagePainter.State.Loading(
                    painter = painter
                )
            )


            Column(
                modifier = Modifier.fillMaxWidth().padding(6.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                stateList.map { state ->
                    Box(
                        modifier = Modifier
                            .requiredWidth(72.dp)
                            .aspectRatio(16 / 9f)
                            .clip(RoundedCornerShape(5.dp))
                            .border(
                                1.dp,
                                Color.Black,
                                RoundedCornerShape(5.dp)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        RemoteImage(
                            painter = painter,
                            state = state
                        )
                    }
                }
            }
        }
    }
}