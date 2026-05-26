package com.srnyndrs.android.briefly.domain.model.content

data class ArticleItem(
    val id: String,
    val title: String,
    val url: String? = null,
    val description: String? = null,
    val source: String? = null,
    val category: String? = null,
    val imageUrl: String? = null,
    val hasContent: Boolean = false,
)
