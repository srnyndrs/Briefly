package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.XMark
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.FilterSource
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.ui.components.SectionHeader
import com.srnyndrs.android.briefly.ui.components.SelectionChip
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class, ExperimentalTime::class)
@Composable
fun ExploreFilterBottomSheet(
    modifier: Modifier = Modifier,
    draftFilter: ExplorePostFilter,
    filterOptions: ExploreFilterOptions,
    onDraftFilterChange: (ExplorePostFilter) -> Unit,
    onApply: () -> Unit,
    onReset: () -> Unit,
    onDismiss: () -> Unit,
) {
    Column(
        modifier = Modifier.then(modifier),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f, fill = false)
                .verticalScroll(rememberScrollState())
                .padding(top = 16.dp, start = 16.dp, end = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header: Title, Close button, and Newspaper dividers
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = stringResource(R.string.explore_filter_title),
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                    )
                    IconButton(
                        modifier = Modifier.size(36.dp),
                        onClick = onDismiss,
                    ) {
                        Icon(
                            imageVector = Heroicons.Solid.XMark,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurface,
                        )
                    }
                }

                HorizontalDivider(
                    thickness = 2.dp,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }

            // Scrollable filter sections
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(20.dp),
            ) {
                // Section 1: Sort
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    SectionHeader(
                        title = stringResource(R.string.explore_filter_section_sort),
                    )

                    val isQueryActive = !draftFilter.query.isNullOrBlank()
                    if (isQueryActive) {
                        Text(
                            text = stringResource(R.string.explore_filter_sort_query_disabled),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                        )
                    } else {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            SelectionChip(
                                label = stringResource(R.string.explore_filter_sort_freshness),
                                selected = draftFilter.sort == null || draftFilter.sort == "freshness",
                                onClick = {
                                    onDraftFilterChange(draftFilter.copy(sort = "freshness"))
                                },
                            )
                            SelectionChip(
                                label = stringResource(R.string.explore_filter_sort_oldest),
                                selected = draftFilter.sort == "oldest",
                                onClick = {
                                    onDraftFilterChange(draftFilter.copy(sort = "oldest"))
                                },
                            )
                        }
                    }
                }

                // Section 2: Publication Date Range
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    SectionHeader(
                        title = stringResource(R.string.explore_filter_section_date),
                    )
                    DateRangeSelector(
                        publishedFrom = draftFilter.publishedFrom,
                        publishedTo = draftFilter.publishedTo,
                        onDateRangeSelected = { from, to ->
                            onDraftFilterChange(
                                draftFilter.copy(
                                    publishedFrom = from,
                                    publishedTo = to,
                                )
                            )
                        },
                        onClearDateRange = {
                            onDraftFilterChange(
                                draftFilter.copy(
                                    publishedFrom = null,
                                    publishedTo = null,
                                )
                            )
                        },
                    )
                }

                // Section 3: Categories
                if (filterOptions.categories.isNotEmpty()) {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        SectionHeader(
                            title = stringResource(R.string.explore_filter_section_categories),
                        )
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            filterOptions.categories.forEach { category ->
                                val isSelected = draftFilter.categories?.contains(category) == true
                                SelectionChip(
                                    label = category,
                                    selected = isSelected,
                                    onClick = {
                                        val currentList = draftFilter.categories.orEmpty()
                                        val updatedList = if (isSelected) {
                                            currentList - category
                                        } else {
                                            currentList + category
                                        }
                                        onDraftFilterChange(
                                            draftFilter.copy(
                                                categories = updatedList.ifEmpty { null }
                                            )
                                        )
                                    },
                                )
                            }
                        }
                    }
                }

                // Section 4: Languages
                if (filterOptions.languages.isNotEmpty()) {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        SectionHeader(
                            title = stringResource(R.string.explore_filter_section_languages),
                        )
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            filterOptions.languages.forEach { language ->
                                val isSelected = draftFilter.languages?.contains(language) == true
                                SelectionChip(
                                    label = language.uppercase(),
                                    selected = isSelected,
                                    onClick = {
                                        val currentList = draftFilter.languages.orEmpty()
                                        val updatedList = if (isSelected) {
                                            currentList - language
                                        } else {
                                            currentList + language
                                        }
                                        onDraftFilterChange(
                                            draftFilter.copy(
                                                languages = updatedList.ifEmpty { null }
                                            )
                                        )
                                    },
                                )
                            }
                        }
                    }
                }

                // Section 5: Sources
                if (filterOptions.sources.isNotEmpty()) {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        SectionHeader(
                            title = stringResource(R.string.explore_filter_section_sources),
                        )
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            filterOptions.sources.forEach { source ->
                                val isSelected = draftFilter.sourceIds?.contains(source.id) == true
                                SelectionChip(
                                    label = source.title,
                                    selected = isSelected,
                                    onClick = {
                                        val currentList = draftFilter.sourceIds.orEmpty()
                                        val updatedList = if (isSelected) {
                                            currentList - source.id
                                        } else {
                                            currentList + source.id
                                        }
                                        onDraftFilterChange(
                                            draftFilter.copy(
                                                sourceIds = updatedList.ifEmpty { null }
                                            )
                                        )
                                    },
                                )
                            }
                        }
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            }
        }

        // Bottom Sticky Actions: Reset All & Apply
        HorizontalDivider(
            thickness = 1.dp,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f),
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedButton(
                modifier = Modifier
                    .weight(1f)
                    .height(48.dp),
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.onSurface),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.onSurface,
                ),
                onClick = onReset,
            ) {
                Text(
                    text = stringResource(R.string.explore_filter_reset),
                    style = MaterialTheme.typography.labelLarge,
                )
            }

            Button(
                modifier = Modifier
                    .weight(1.5f)
                    .height(48.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.onSurface,
                    contentColor = MaterialTheme.colorScheme.surface,
                ),
                onClick = onApply,
            ) {
                Text(
                    text = stringResource(R.string.explore_filter_apply),
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTime::class)
@PreviewLightDark
@Composable
fun ExploreFilterBottomSheetPreview() {
    BrieflyTheme {
        Surface {
            ExploreFilterBottomSheet(
                modifier = Modifier.fillMaxSize(),
                draftFilter = ExplorePostFilter(
                    categories = listOf("Politics"),
                    languages = listOf("en"),
                ),
                filterOptions = ExploreFilterOptions(
                    categories = listOf("Politics", "Business", "Technology", "Science", "Culture"),
                    languages = listOf("en", "hu", "de"),
                    sources = listOf(
                        FilterSource("1", "The New York Times"),
                        FilterSource("2", "BBC News"),
                        FilterSource("3", "Reuters"),
                    ),
                ),
                onDraftFilterChange = {},
                onApply = {},
                onReset = {},
                onDismiss = {},
            )
        }
    }
}
