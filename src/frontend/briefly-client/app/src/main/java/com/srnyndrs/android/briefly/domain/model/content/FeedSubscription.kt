package com.srnyndrs.android.briefly.domain.model.content

import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class FeedSubscription(
    val userId: String,
    val sourceId: String,
    val createdAt: Instant,
)
