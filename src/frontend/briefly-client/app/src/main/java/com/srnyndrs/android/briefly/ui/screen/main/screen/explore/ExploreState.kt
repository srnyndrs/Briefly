package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
data class ExploreState(
    val query: String = "",
    val filter: ExplorePostFilter = ExplorePostFilter(sort = "freshness"),
    val draftFilter: ExplorePostFilter = ExplorePostFilter(sort = "freshness"),
    val isFilterSheetOpen: Boolean = false,
    val filterOptions: ExploreFilterOptions = ExploreFilterOptions(),
) {
    val activeFilterCount: Int
        get() {
            var count = 0
            if (filter.sort != null && filter.sort != "freshness") count++
            if (filter.publishedFrom != null || filter.publishedTo != null) count++
            if (!filter.categories.isNullOrEmpty()) count += filter.categories.size
            if (!filter.languages.isNullOrEmpty()) count += filter.languages.size
            if (!filter.sourceIds.isNullOrEmpty()) count += filter.sourceIds.size
            return count
        }

    val hasActiveFilters: Boolean
        get() = activeFilterCount > 0
}
