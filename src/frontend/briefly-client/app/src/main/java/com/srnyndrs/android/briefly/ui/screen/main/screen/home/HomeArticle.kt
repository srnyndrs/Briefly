package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.Post

// Keep the request identity when Paging retains rows across generations.
data class HomeArticle(
    val post: Post,
    val category: Category?,
)
