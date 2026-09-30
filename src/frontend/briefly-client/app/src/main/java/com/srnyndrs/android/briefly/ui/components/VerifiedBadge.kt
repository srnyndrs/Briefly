package com.srnyndrs.android.briefly.ui.components


import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Check
import com.composables.icons.heroicons.solid.CheckBadge
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.WavyCircleShape

@Composable
fun VerifiedBadge(
    modifier: Modifier = Modifier,
    containerColor: Color = MaterialTheme.colorScheme.primaryContainer,
    contentColor: Color = MaterialTheme.colorScheme.surface,
    wavesCount: Int = 8,
    waveAmplitude: Float = 4f,
) {
    Column(
        modifier = Modifier.then(modifier)
    ) {
        Icon(
            modifier = Modifier
                .fillMaxSize()
                .clip(WavyCircleShape(wavesCount, waveAmplitude))
                .background(containerColor)
                .padding(6.dp),
            imageVector = Heroicons.Outline.Check,
            tint = contentColor,
            contentDescription = null,
        )
    }
}

@Composable
fun OutlinedVerifiedBadge(
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.primaryContainer,
    innerPadding: Dp = 6.dp,
    wavesCount: Int = 8,
    waveAmplitude: Float = 4f,
) {
    Column(
        modifier = Modifier.then(modifier)
    ) {
        Icon(
            modifier = Modifier
                .fillMaxSize()
                .border(
                    1.dp,
                    color,
                    WavyCircleShape(wavesCount, waveAmplitude)
                )
                .padding(innerPadding),
            imageVector = Heroicons.Outline.Check,
            tint = color,
            contentDescription = null,
        )
    }
}

@PreviewLightDark
@Composable
fun VerifiedBadgePreview() {
    BrieflyTheme {
        Surface {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                VerifiedBadge(
                    modifier = Modifier.size(32.dp)
                )
                OutlinedVerifiedBadge(
                    modifier = Modifier.size(32.dp)
                )
            }
        }
    }
}
