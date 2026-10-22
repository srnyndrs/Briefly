package com.srnyndrs.android.briefly.domain.model.preferences

data class UserPreferences(
    val mutedKeywords: List<String>,
    val mutedCategories: List<String>,
    val blockedSourceIds: Set<String>,
    val languages: Set<String>,
)
