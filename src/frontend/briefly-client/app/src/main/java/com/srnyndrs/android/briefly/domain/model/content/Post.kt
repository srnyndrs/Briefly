package com.srnyndrs.android.briefly.domain.model.content

import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class Post(
    val id: String,
    val title: String,
    val url: String? = null,
    val description: String? = null,
    val source: String? = null,
    val category: String? = null,
    val imageUrl: String? = null,
    val publishDate: Instant? = null,
    val hasContent: Boolean = false,
)
