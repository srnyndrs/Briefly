package com.srnyndrs.android.briefly.domain.model.content

import kotlin.time.Instant
import kotlin.time.ExperimentalTime

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
