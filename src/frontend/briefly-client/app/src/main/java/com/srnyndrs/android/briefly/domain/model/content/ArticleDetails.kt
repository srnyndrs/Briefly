package com.srnyndrs.android.briefly.domain.model.content

import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class ArticleDetails(
    val id: String,
    val title: String,
    val source: String? = null,
    val category: String? = null,
    val url: String? = null,
    val publishedAt: Instant,
    val language: String? = null,
    val content: String? = null,
    val imageUrl: String? = null
)
