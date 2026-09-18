package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.FilterSource
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.Instant as JavaInstant
import kotlin.time.ExperimentalTime

private val activeDateFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("d MMM")

@OptIn(ExperimentalTime::class)
@Composable
fun ExploreActiveFiltersRow(
    modifier: Modifier = Modifier,
    filter: ExplorePostFilter,
    filterOptions: ExploreFilterOptions,
    onRemoveCategory: (String) -> Unit,
    onRemoveLanguage: (String) -> Unit,
    onRemoveSource: (String) -> Unit,
    onClearDateRange: () -> Unit,
    onResetSort: () -> Unit,
    onClearAll: () -> Unit,
) {
    val dateRangeText = remember(filter.publishedFrom, filter.publishedTo) {
        when {
            filter.publishedFrom != null && filter.publishedTo != null -> {
                val from = JavaInstant.ofEpochMilli(filter.publishedFrom.toEpochMilliseconds())
                    .atZone(ZoneId.systemDefault())
                val to = JavaInstant.ofEpochMilli(filter.publishedTo.toEpochMilliseconds())
                    .atZone(ZoneId.systemDefault())
                "${activeDateFormatter.format(from)} – ${activeDateFormatter.format(to)}"
            }
            filter.publishedFrom != null -> {
                val from = JavaInstant.ofEpochMilli(filter.publishedFrom.toEpochMilliseconds())
                    .atZone(ZoneId.systemDefault())
                "From: ${activeDateFormatter.format(from)}"
            }
            filter.publishedTo != null -> {
                val to = JavaInstant.ofEpochMilli(filter.publishedTo.toEpochMilliseconds())
                    .atZone(ZoneId.systemDefault())
                "To: ${activeDateFormatter.format(to)}"
            }
            else -> null
        }
    }

    val sourceTitleMap = remember(filterOptions.sources) {
        filterOptions.sources.associate { it.id to it.title }
    }

    LazyRow(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(horizontal = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Clear all text button
        item(key = "clear_all") {
            Box(
                modifier = Modifier
                    .clickable(onClick = onClearAll)
                    .padding(horizontal = 6.dp, vertical = 6.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = stringResource(R.string.explore_filter_clear_all),
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    textDecoration = TextDecoration.Underline,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }
        }

        // Sort filter
        if (filter.sort != null && filter.sort != "freshness") {
            item(key = "sort_${filter.sort}") {
                ActiveFilterChip(
                    label = "Sort: ${filter.sort.replaceFirstChar { it.uppercase() }}",
                    onRemove = onResetSort,
                )
            }
        }

        // Date range filter
        dateRangeText?.let { text ->
            item(key = "date_range") {
                ActiveFilterChip(
                    label = text,
                    onRemove = onClearDateRange,
                )
            }
        }

        // Category filters
        filter.categories?.let { categories ->
            items(categories, key = { "cat_$it" }) { category ->
                ActiveFilterChip(
                    label = category,
                    onRemove = { onRemoveCategory(category) },
                )
            }
        }

        // Language filters
        filter.languages?.let { languages ->
            items(languages, key = { "lang_$it" }) { language ->
                ActiveFilterChip(
                    label = "Lang: ${language.uppercase()}",
                    onRemove = { onRemoveLanguage(language) },
                )
            }
        }

        // Source filters
        filter.sourceIds?.let { sourceIds ->
            items(sourceIds, key = { "source_$it" }) { sourceId ->
                val title = sourceTitleMap[sourceId] ?: sourceId
                ActiveFilterChip(
                    label = title,
                    onRemove = { onRemoveSource(sourceId) },
                )
            }
        }
    }
}

@OptIn(ExperimentalTime::class)
@PreviewLightDark
@Composable
fun ExploreActiveFiltersRowPreview() {
    BrieflyTheme {
        Surface {
            ExploreActiveFiltersRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                filter = ExplorePostFilter(
                    categories = listOf("Technology", "Science"),
                    languages = listOf("en"),
                    sort = "oldest",
                ),
                filterOptions = ExploreFilterOptions(
                    categories = listOf("Technology", "Science"),
                    languages = listOf("en"),
                    sources = listOf(FilterSource(id = "1", title = "The Verge")),
                ),
                onRemoveCategory = {},
                onRemoveLanguage = {},
                onRemoveSource = {},
                onClearDateRange = {},
                onResetSort = {},
                onClearAll = {},
            )
        }
    }
}

