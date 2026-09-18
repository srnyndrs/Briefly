package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter

sealed interface ExploreEvent {
    data class UpdateQuery(val query: String) : ExploreEvent
    data object SubmitQuery : ExploreEvent
    data object ClearQuery : ExploreEvent

    data object OpenFilterSheet : ExploreEvent
    data object DismissFilterSheet : ExploreEvent
    data class UpdateDraftFilter(val filter: ExplorePostFilter) : ExploreEvent
    data object ApplyDraftFilter : ExploreEvent
    data object ResetDraftFilters : ExploreEvent

    data class RemoveCategory(val category: String) : ExploreEvent
    data class RemoveLanguage(val language: String) : ExploreEvent
    data class RemoveSource(val sourceId: String) : ExploreEvent
    data object ClearDateRange : ExploreEvent
    data class ChangeSort(val sort: String) : ExploreEvent
    data object ClearAllFilters : ExploreEvent
}
