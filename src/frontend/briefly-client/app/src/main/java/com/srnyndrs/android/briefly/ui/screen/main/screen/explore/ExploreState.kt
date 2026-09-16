package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
data class ExploreState(
    val query: String = "",
    val filter: ExplorePostFilter = ExplorePostFilter(sort = "freshness"),
)
