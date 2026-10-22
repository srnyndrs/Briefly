package com.srnyndrs.android.briefly.domain.model.content.post

import com.srnyndrs.android.briefly.domain.model.content.Category
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
data class PostDetails(
    val id: String,
    val title: String,
    val sourceId: String? = null,
    val sourceTitle: String? = null,
    val categories: List<Category> = emptyList(),
    val url: String? = null,
    val publishedAt: Instant? = null,
    val language: String? = null,
    val content: String? = null,
    val author: String? = null,
    val keywords: List<String> = emptyList(),
    val imageUrl: String? = null,
)
