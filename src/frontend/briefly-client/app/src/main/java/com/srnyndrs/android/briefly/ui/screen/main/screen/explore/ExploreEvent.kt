package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

sealed interface ExploreEvent {
    data class UpdateQuery(val query: String): ExploreEvent
    data object SubmitQuery: ExploreEvent
    data class ChangeSort(val sort: String): ExploreEvent
    data object ClearFilters: ExploreEvent
}
