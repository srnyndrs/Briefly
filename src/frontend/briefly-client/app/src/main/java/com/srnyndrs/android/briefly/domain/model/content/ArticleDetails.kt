package com.srnyndrs.android.briefly.domain.model.content

data class ArticleDetails(
    val id: String,
    val title: String,
    val content: String? = null,
    val imageUrl: String? = null
)
