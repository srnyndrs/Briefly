package com.srnyndrs.android.briefly.ui.navigation

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.colorResource
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun SessionSplash(
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = Modifier.then(modifier)
            .background(colorResource(R.color.splash_background)),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .size(108.dp)
                .background(colorResource(R.color.splash_icon_background)),
        ) {
            Image(
                modifier = Modifier.fillMaxSize(),
                painter = painterResource(R.drawable.ic_launcher_foreground),
                contentDescription = null,
            )
        }
    }
}

@PreviewLightDark
@Composable
fun SessionSplashPreview() {
    BrieflyTheme {
        Surface {
            SessionSplash(
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}
