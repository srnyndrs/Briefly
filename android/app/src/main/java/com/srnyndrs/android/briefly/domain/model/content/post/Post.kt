package com.srnyndrs.android.briefly.domain.model.content.post

import com.srnyndrs.android.briefly.domain.model.content.Category
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class Post(
    val id: String,
    val title: String,
    val url: String? = null,
    val description: String? = null,
    val sourceTitle: String? = null,
    val categories: List<Category> = emptyList(),
    val imageUrl: String? = null,
    val publishedAt: Instant? = null,
    val hasContent: Boolean = false,
)
