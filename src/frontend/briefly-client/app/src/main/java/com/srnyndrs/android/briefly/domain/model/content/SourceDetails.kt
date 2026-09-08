package com.srnyndrs.android.briefly.domain.model.content

import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class SourceDetails(
    val id: String,
    val title: String?,
    val description: String? = null,
    val websiteUrl: String? = null,
    val imageUrl: String? = null,
    val subscribed: Boolean = false,
    val followed: Boolean = false, // NOT YET IMPLEMENTED
    val lastUpdatedAt: Instant
)
