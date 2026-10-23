package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.util.InstantIso8601Serializer
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlinx.serialization.*

@Serializable
data class FeedRequestDto(
    val page: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    val category: String? = null,

    @SerialName("include_filter_options")
    val includeFilterOptions: Boolean = false,
)

@Serializable
data class ExploreRequestDto(
    val page: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    val categories: List<String>? = null,
    val languages: List<String>? = null,

    @SerialName("source_ids")
    val sourceIds: List<String>? = null,

    @SerialName("from")
    val publishedFrom: String? = null,

    val query: String? = null,

    @SerialName("to")
    val publishedTo: String? = null,

    val sort: String? = null,

    @SerialName("apply_user_preferences")
    val applyUserPreferences: Boolean = true,

    @SerialName("include_filter_options")
    val includeFilterOptions: Boolean = false,
)

@Serializable
data class PostListItemsResponseDto(
    val items: List<PostSummaryResponseDto>,
    val total: Long,
    val page: Int = 1,

    @SerialName("page_count")
    val pageCount: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    @SerialName("filter_options")
    val filterOptions: FilterOptionsDto? = null,
)

@Serializable
data class PersonalFeedResponseDto(
    val headlines: List<PostSummaryResponseDto>? = null,
    val items: List<PostSummaryResponseDto>,
    val total: Long,
    val page: Int = 1,

    @SerialName("page_count")
    val pageCount: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    @SerialName("filter_options")
    val filterOptions: FilterOptionsDto? = null,
)

@Serializable
data class FilterOptionsDto(
    val categories: List<String> = emptyList(),
    val languages: List<String> = emptyList(),
    val authors: List<String> = emptyList(),
    val keywords: List<String> = emptyList(),
    val sources: List<SourceEntry> = emptyList(),
)

@Serializable
data class SourceEntry(
    val id: String,
    val title: String,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class PostSummaryResponseDto(
    @SerialName("post_id")
    val postId: String,

    @SerialName("source_id")
    val sourceId: String? = null,

    val title: String,

    @SerialName("source_title")
    val sourceTitle: String? = null,

    val description: String? = null,

    @SerialName("canonical_url")
    val canonicalUrl: String? = null,

    val language: String? = null,
    val categories: List<String>? = null,

    @SerialName("image_ref")
    val imageRef: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("published_at")
    val publishedAt: Instant?,

    @SerialName("has_content")
    val hasContent: Boolean,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class PostResponseDto(
    @SerialName("post_id")
    val postId: String,

    @SerialName("source_id")
    val sourceId: String? = null,

    val title: String,

    @SerialName("source_title")
    val sourceTitle: String? = null,

    val description: String? = null,

    @SerialName("canonical_url")
    val canonicalUrl: String? = null,

    val language: String? = null,
    val categories: List<String>? = null,

    @SerialName("image_ref")
    val imageRef: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("published_at")
    val publishedAt: Instant?,

    val content: String? = null,
    val author: String? = null,
    val keywords: List<String> = emptyList(),
)
