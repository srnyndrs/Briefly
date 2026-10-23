package com.srnyndrs.android.briefly.domain.model.profile

import com.srnyndrs.android.briefly.domain.model.preferences.UserPreferences

data class Profile(
    val email: String,
    val preferences: UserPreferences,
)
