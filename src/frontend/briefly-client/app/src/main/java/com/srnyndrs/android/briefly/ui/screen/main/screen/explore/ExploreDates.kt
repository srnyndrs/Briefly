package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import java.time.Instant as JavaInstant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale
import kotlin.time.Duration.Companion.days
import kotlin.time.Duration.Companion.nanoseconds
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

// Material date pickers represent calendar dates as UTC midnight.
@OptIn(ExperimentalTime::class)
internal fun selectedDateStart(millis: Long): Instant =
    Instant.fromEpochMilliseconds(epochMilliseconds = millis)

@OptIn(ExperimentalTime::class)
internal fun selectedDateEnd(millis: Long): Instant =
    selectedDateStart(millis = millis) + 1.days - 1.nanoseconds

@OptIn(ExperimentalTime::class)
internal fun formatExploreDate(
    instant: Instant,
    locale: Locale,
): String = DateTimeFormatter
    .ofLocalizedDate(FormatStyle.MEDIUM)
    .withLocale(locale)
    .format(JavaInstant.ofEpochMilli(instant.toEpochMilliseconds()).atZone(ZoneOffset.UTC))
