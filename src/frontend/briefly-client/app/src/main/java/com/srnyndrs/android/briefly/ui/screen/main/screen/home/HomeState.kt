package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import com.srnyndrs.android.briefly.domain.model.content.Post

data class HomeState(
    val headlines: List<Post> = emptyList(),
    val categories: List<String> = emptyList(),
    val selectedCategory: String? = null,
)
