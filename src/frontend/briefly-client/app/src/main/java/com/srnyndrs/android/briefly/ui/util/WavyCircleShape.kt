package com.srnyndrs.android.briefly.ui.util

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Outline
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import kotlin.math.cos
import kotlin.math.sin

class WavyCircleShape(
    private val wavesCount: Int = 9,
    private val waveAmplitude: Float = 12f
) : Shape {
    override fun createOutline(
        size: Size,
        layoutDirection: LayoutDirection,
        density: Density
    ): Outline {
        val path = Path()
        val centerX = size.width / 2f
        val centerY = size.height / 2f
        val baseRadius = (size.minDimension / 2f) - waveAmplitude

        val step = 2.0 * Math.PI / 360.0

        for (i in 0 until 360) {
            val angle = i * step
            val currentRadius = baseRadius + (sin(angle * wavesCount) * waveAmplitude)

            val x = centerX + (cos(angle) * currentRadius).toFloat()
            val y = centerY + (sin(angle) * currentRadius).toFloat()

            if (i == 0) {
                path.moveTo(x, y)
            } else {
                path.lineTo(x, y)
            }
        }
        path.close()

        return Outline.Generic(path)
    }
}

@Preview
@Composable
fun WavyCirclePreview() {
    Box(
        modifier = Modifier
            .size(200.dp)
            .background(
                color = Color(0xFF6200EE),
                shape = WavyCircleShape(wavesCount = 9, waveAmplitude = 12f)
            )
    )
}
