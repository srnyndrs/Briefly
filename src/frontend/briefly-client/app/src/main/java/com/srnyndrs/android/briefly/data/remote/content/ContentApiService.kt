package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.ArticleDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedResultDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceResultItemDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeResponseDto
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.delete
import io.ktor.client.request.get
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.HttpStatusCode

class ContentApiService (
    private val client: HttpClient
) {
    suspend fun getFeed(page: Int? = 1, pageSize: Int? = 20, sourceIds: List<String>? = null): FeedResultDto {
        return client.get("feed") {
            parameter("page", page ?: 1)
            parameter("page_size", pageSize ?: 20)
            sourceIds?.forEach { id ->
                parameter("source_ids", id)
            }
            parameter("subscribed_only", sourceIds == null)
        }.body()
    }

    suspend fun getFeedSources(query: String? = null): List<FeedSourceDto> {
        return client.get("sources") {
            parameter("query", query ?: "")
        }.body()
    }

    suspend fun getFeedSourceSubscriptions(): List<FeedSourceSubscribeResponseDto> {
        return client.get("me/subscriptions")
            .body()
    }

    suspend fun subscribeFeedSource(request: FeedSourceSubscribeRequestDto): FeedSourceSubscribeResponseDto {
        return client.post("me/subscriptions") {
            setBody(request)
        }.body()
    }

    suspend fun unsubscribeFeedSource(sourceId: String): HttpStatusCode {
        return client.delete("me/subscriptions/${sourceId}")
            .status
    }

    suspend fun getFeedSourceDetails(sourceId: String): FeedSourceDetailsDto {
        return client.get("sources/${sourceId}")
            .body()
    }

    suspend fun getPostById(postId: String): ArticleDetailsDto {
        return client.get("posts/${postId}")
            .body()
    }

}
