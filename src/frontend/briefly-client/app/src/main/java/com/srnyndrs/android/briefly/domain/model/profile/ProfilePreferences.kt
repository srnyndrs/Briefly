package com.srnyndrs.android.briefly.domain.model.profile

data class ProfilePreferences (
    val mutedKeywords: List<String>,
    val mutedCategories: List<String>,
    val categoryInterests: List<String>,
    val blockedSourceIds: Set<String>,
    val languages: Set<String>,
)
