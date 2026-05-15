package com.srnyndrs.android.briefly.data.remote.content.dto

import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class FeedResultDto (
    val items: List<FeedResultItemDto>,
    val total: Long
)

@Serializable
data class FeedResultItemDto (
    @SerialName("article_id")
    val articleID: String,

    @SerialName("source_id")
    val sourceID: String,

    val title: String,

    @SerialName("canonical_url")
    val canonicalURL: String,

    val language: JsonElement? = null,
    val categories: JsonArray,

    @SerialName("content_ref")
    val contentRef: String,

    @SerialName("image_ref")
    val imageRef: String? = null,

    val sentiment: String,
    val topics: JsonArray,

    @SerialName("published_at")
    val publishedAt: String
)

@Serializable
data class FeedSourceExploreRequestDto(
    val url: String,
)

@Serializable
data class FeedSourceResultItemDto(
    val url: String,
    val title: String,

    @SerialName("content_type")
    val contentType: String? = null,

    val favicon: String? = null,
    val description: String? = null
)


@Serializable
data class ArticleDetailsDto (
    @SerialName("article_id")
    val articleId: String,

    @SerialName("source_id")
    val sourceID: String,

    val title: String,

    @SerialName("canonical_url")
    val canonicalURL: String,

    val language: String? = null,
    val categories: List<String>,

    @SerialName("content_ref")
    val contentRef: String,

    val content: String? = null,

    @SerialName("image_ref")
    val imageRef: String? = null,

    val sentiment: String,
    val topics: List<String>,

    @SerialName("published_at")
    val publishedAt: String,

    @SerialName("cluster_id")
    val clusterID: String? = null,

    @SerialName("model_version")
    val modelVersion: String
)
