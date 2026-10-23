package com.srnyndrs.android.briefly.domain.model.content.feed

import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.Post

data class HomeFeedMetadata(
    val headlines: List<Post>,
    val categories: List<Category>,
)
