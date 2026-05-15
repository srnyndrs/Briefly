package com.srnyndrs.android.briefly.domain.model.content

data class ArticleItem(
    val id: String,
    val title: String,
    val description: String,
    val source: String? = null, // TODO
    val imageUrl: String? = null,
)
