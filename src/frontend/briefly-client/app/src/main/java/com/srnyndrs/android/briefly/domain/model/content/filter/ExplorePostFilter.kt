package com.srnyndrs.android.briefly.domain.model.content.filter

import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class ExplorePostFilter(
    val query: String? = null,
    val categories: List<String>? = null,
    val languages: List<String>? = null,
    val sourceIds: List<String>? = null,
    val publishedFrom: Instant? = null,
    val publishedTo: Instant? = null,
    val sort: String? = null,
)
