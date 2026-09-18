package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.DateRangePicker
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDateRangePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Calendar
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import java.time.Instant as JavaInstant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

private val dateFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("d MMM yyyy")

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTime::class)
@Composable
fun DateRangeSelector(
    modifier: Modifier = Modifier,
    publishedFrom: Instant?,
    publishedTo: Instant?,
    onDateRangeSelected: (Instant?, Instant?) -> Unit,
    onClearDateRange: () -> Unit,
) {
    var showDialog by remember { mutableStateOf(false) }

    val shape = RoundedCornerShape(12.dp)
    val hasDateSelected = publishedFrom != null || publishedTo != null

    val fromText = remember(publishedFrom) {
        publishedFrom?.let {
            val javaInstant = JavaInstant.ofEpochMilli(it.toEpochMilliseconds())
            dateFormatter.format(javaInstant.atZone(ZoneId.systemDefault()))
        }
    }

    val toText = remember(publishedTo) {
        publishedTo?.let {
            val javaInstant = JavaInstant.ofEpochMilli(it.toEpochMilliseconds())
            dateFormatter.format(javaInstant.atZone(ZoneId.systemDefault()))
        }
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            // "From" card
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(shape)
                    .border(
                        width = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f),
                        shape = shape,
                    )
                    .background(
                        if (publishedFrom != null) {
                            MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f)
                        } else {
                            MaterialTheme.colorScheme.surface
                        }
                    )
                    .clickable { showDialog = true }
                    .padding(horizontal = 12.dp, vertical = 10.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = stringResource(R.string.explore_filter_date_from),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        )
                        Text(
                            text = fromText ?: stringResource(R.string.explore_filter_date_any),
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = if (fromText != null) FontWeight.SemiBold else FontWeight.Normal,
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                    }
                    Icon(
                        modifier = Modifier.size(18.dp),
                        imageVector = Heroicons.Outline.Calendar,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    )
                }
            }

            // "To" card
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(shape)
                    .border(
                        width = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f),
                        shape = shape,
                    )
                    .background(
                        if (publishedTo != null) {
                            MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f)
                        } else {
                            MaterialTheme.colorScheme.surface
                        }
                    )
                    .clickable { showDialog = true }
                    .padding(horizontal = 12.dp, vertical = 10.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = stringResource(R.string.explore_filter_date_to),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        )
                        Text(
                            text = toText ?: stringResource(R.string.explore_filter_date_any),
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = if (toText != null) FontWeight.SemiBold else FontWeight.Normal,
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                    }
                    Icon(
                        modifier = Modifier.size(18.dp),
                        imageVector = Heroicons.Outline.Calendar,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    )
                }
            }
        }

        if (hasDateSelected) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onClearDateRange) {
                    Text(
                        text = stringResource(R.string.explore_filter_date_clear),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }
        }
    }

    if (showDialog) {
        val pickerState = rememberDateRangePickerState(
            initialSelectedStartDateMillis = publishedFrom?.toEpochMilliseconds(),
            initialSelectedEndDateMillis = publishedTo?.toEpochMilliseconds(),
        )

        DatePickerDialog(
            onDismissRequest = { showDialog = false },
            confirmButton = {
                TextButton(
                    onClick = {
                        val startMillis = pickerState.selectedStartDateMillis
                        val endMillis = pickerState.selectedEndDateMillis
                        val fromInstant = startMillis?.let { Instant.fromEpochMilliseconds(it) }
                        val toInstant = endMillis?.let { Instant.fromEpochMilliseconds(it) }
                        onDateRangeSelected(fromInstant, toInstant)
                        showDialog = false
                    },
                ) {
                    Text(
                        text = stringResource(R.string.explore_filter_confirm),
                        style = MaterialTheme.typography.labelLarge,
                    )
                }
            },
            dismissButton = {
                TextButton(onClick = { showDialog = false }) {
                    Text(
                        text = stringResource(R.string.explore_filter_cancel),
                        style = MaterialTheme.typography.labelLarge,
                    )
                }
            },
            colors = DatePickerDefaults.colors(
                containerColor = MaterialTheme.colorScheme.surface,
            ),
        ) {
            DateRangePicker(
                state = pickerState,
                title = {
                    Text(
                        modifier = Modifier.padding(start = 24.dp, top = 16.dp),
                        text = stringResource(R.string.explore_filter_date_select_range),
                        style = MaterialTheme.typography.titleMedium,
                    )
                },
                colors = DatePickerDefaults.colors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface,
                    headlineContentColor = MaterialTheme.colorScheme.onSurface,
                    weekdayContentColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                    subheadContentColor = MaterialTheme.colorScheme.onSurface,
                    yearContentColor = MaterialTheme.colorScheme.onSurface,
                    currentYearContentColor = MaterialTheme.colorScheme.onSurface,
                    selectedYearContainerColor = MaterialTheme.colorScheme.onSurface,
                    selectedYearContentColor = MaterialTheme.colorScheme.surface,
                    dayContentColor = MaterialTheme.colorScheme.onSurface,
                    selectedDayContainerColor = MaterialTheme.colorScheme.onSurface,
                    selectedDayContentColor = MaterialTheme.colorScheme.surface,
                    dayInSelectionRangeContainerColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.15f),
                    dayInSelectionRangeContentColor = MaterialTheme.colorScheme.onSurface,
                ),
            )
        }
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun DateRangeSelectorPreview() {
    BrieflyTheme {
        Surface {
            DateRangeSelector(
                modifier = Modifier.padding(16.dp),
                publishedFrom = Instant.fromEpochMilliseconds(1726500000000L),
                publishedTo = Instant.fromEpochMilliseconds(1727000000000L),
                onDateRangeSelected = { _, _ -> },
                onClearDateRange = {},
            )
        }
    }
}

