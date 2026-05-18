package com.srnyndrs.android.briefly.ui.util

import android.content.Context
import android.net.Uri
import android.text.format.DateUtils
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
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

    // Optional: You can customize the toolbar color to match your app theme here
    // builder.setDefaultColorSchemeParams(...)

    val customTabsIntent = builder.build()

    try {
        customTabsIntent.launchUrl(context, url.toUri())
    } catch (e: Exception) {
        // Fallback in case the user has no browser installed that supports Custom Tabs
        // You could launch a standard Intent.ACTION_VIEW here
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
