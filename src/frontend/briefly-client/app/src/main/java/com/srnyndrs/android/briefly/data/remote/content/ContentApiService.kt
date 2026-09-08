package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.PostResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceDetailsResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceDiscoverRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceDiscoveryResultDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SubscriptionCreateRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SubscriptionResponseDto
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

    suspend fun getFeed(page: Int? = 1, pageSize: Int? = 20, sourceIds: List<String>? = null): FeedResponseDto {
        return client.get("feed") {
            parameter("page", page ?: 1)
            parameter("page_size", pageSize ?: 20)
            sourceIds?.forEach { id ->
                parameter("source_ids", id)
            }
            parameter("subscribed_only", sourceIds == null)
        }.body()
    }

    suspend fun getFeedSources(query: String? = null): List<SourceResponseDto> {
        return client.get("sources") {
            parameter("query", query ?: "")
        }.body()
    }

    suspend fun discoverSources(request: SourceDiscoverRequestDto): List<SourceDiscoveryResultDto> {
        return client.post("sources/discover") {
            setBody(request)
        }.body()
    }

    suspend fun getFeedSourceSubscriptions(): List<SubscriptionResponseDto> {
        return client.get("me/subscriptions")
            .body()
    }

    suspend fun subscribeFeedSource(request: SubscriptionCreateRequestDto): SubscriptionResponseDto {
        return client.post("me/subscriptions") {
            setBody(request)
        }.body()
    }

    suspend fun unsubscribeFeedSource(sourceId: String): HttpStatusCode {
        return client.delete("me/subscriptions/${sourceId}")
            .status
    }

    suspend fun getFeedSourceDetails(sourceId: String): SourceDetailsResponseDto {
        return client.get("sources/${sourceId}")
            .body()
    }

    suspend fun getPostById(postId: String): PostResponseDto {
        return client.get("posts/${postId}")
            .body()
    }

}
