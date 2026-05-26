package com.srnyndrs.android.briefly.ui.util

import android.content.Context
import android.text.format.DateUtils
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import kotlinx.datetime.TimeZone
import kotlinx.datetime.toJavaLocalDateTime
import kotlinx.datetime.toLocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

fun openCustomTab(context: Context, url: String) {
    val builder = CustomTabsIntent.Builder()
    // builder.setDefaultColorSchemeParams(...)

    val customTabsIntent = builder.build()

    try {
        customTabsIntent.launchUrl(context, url.toUri())
    } catch (_: Exception) {
        // Fallback in case the user has no browser installed that supports Custom Tabs
    }
}

@OptIn(ExperimentalTime::class)
@Composable
fun Instant.toFormattedDateString(): String {
    val formatter = remember {
        DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM)
    }
    val localTime = this.toLocalDateTime(TimeZone.currentSystemDefault())
    return formatter.format(localTime.toJavaLocalDateTime())
}

@OptIn(ExperimentalTime::class)
@Composable
fun Instant.toRelativeArticleTime(): String {
    val timeInMillis = this.toEpochMilliseconds()
    val nowInMillis = System.currentTimeMillis()

    return DateUtils.getRelativeTimeSpanString(
        timeInMillis,
        nowInMillis,
        DateUtils.MINUTE_IN_MILLIS
    ).toString()
}

@Composable
fun Modifier.shimmer(cornerRadius: Dp = 0.dp): Modifier {
    val shimmerColors = listOf(
        Color.LightGray.copy(alpha = 0.3f),
        Color.White.copy(alpha = 0.6f),
        Color.LightGray.copy(alpha = 0.3f)
    )

    val transition = rememberInfiniteTransition(label = "Shimmer")
    val translateAnim by transition.animateFloat(
        initialValue = -400f,
        targetValue = 1200f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = 1600,
                easing = FastOutSlowInEasing
            )
        ),
        label = "Translate"
    )

    return this.drawWithCache {
        val brush = Brush.linearGradient(
            colors = shimmerColors,
            start = Offset(translateAnim, 0f),
            end = Offset(translateAnim + size.width / 1.5f, size.height)
        )
        val cornerPx = cornerRadius.toPx()
        onDrawWithContent {
            drawRoundRect(
                brush = brush,
                cornerRadius = CornerRadius(cornerPx, cornerPx),
                size = size
            )
        }
    }
}

@Composable
fun Modifier.shimmer(isLoading: Boolean, cornerRadius: Dp = 0.dp): Modifier {
    return if (isLoading) this.shimmer(cornerRadius = cornerRadius) else this
}
