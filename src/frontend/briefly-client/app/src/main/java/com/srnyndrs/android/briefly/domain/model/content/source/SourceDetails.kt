package com.srnyndrs.android.briefly.domain.model.content.source

import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class SourceDetails(
    val id: String,
    val title: String?,
    val description: String? = null,
    val siteUrl: String? = null,
    val faviconUrl: String? = null,
    val isSubscribed: Boolean = false,
    val verified: Boolean = false,
    val lastUpdatedAt: Instant,
)
