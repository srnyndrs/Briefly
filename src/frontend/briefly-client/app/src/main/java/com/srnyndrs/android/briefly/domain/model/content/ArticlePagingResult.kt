package com.srnyndrs.android.briefly.domain.model.content

data class ArticlePagingResult(
    val page: Int,
    val count: Int,
    val items: List<ArticleItem>,
)
