package com.srnyndrs.android.briefly.data.remote.profile.dto

import com.srnyndrs.android.briefly.data.utils.InstantIso8601Serializer
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@Serializable
@OptIn(ExperimentalTime::class)
data class ProfileDataResponseDto (
    @SerialName("user_id")
    val userId: String,

    val email: String,

    @SerialName("display_name")
    val displayName: String? = null,

    @SerialName("created_at")
    @Serializable(with = InstantIso8601Serializer::class)
    val createdAt: Instant?,

    val preferences: PreferencesDto
)

@Serializable
data class PreferencesDto (
    @SerialName("user_id")
    val userId: String,

    @SerialName("muted_keywords")
    val mutedKeywords: List<String>,

    @SerialName("muted_categories")
    val mutedCategories: List<String>,

    @SerialName("blocked_source_ids")
    val blockedSourceIds: List<String>,

    val languages: List<String>,

    @SerialName("updated_at")
    val updatedAt: String
)

@Serializable
data class PreferenceUpdateRequestDto (
    @SerialName("muted_keywords")
    val mutedKeywords: List<String>,

    @SerialName("muted_categories")
    val mutedCategories: List<String>,

    @SerialName("blocked_source_ids")
    val blockedSourceIds: List<String>,

    val languages: List<String>,
)
