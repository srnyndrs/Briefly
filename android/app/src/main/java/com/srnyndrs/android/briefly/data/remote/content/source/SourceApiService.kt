package com.srnyndrs.android.briefly.data.remote.content.source

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.delete
import io.ktor.client.request.get
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.HttpStatusCode

class SourceApiService(
    private val client: HttpClient,
) {

    companion object {
        private const val BASE_SOURCES_PATH = "sources"
        private const val BASE_ME_PATH = "me"
        private const val SUBSCRIPTIONS_PATH = "subscriptions"
    }

    suspend fun getFeedSources(query: String? = null): List<SourceResponseDto> {
        return client.get(BASE_SOURCES_PATH) {
            parameter("query", query.orEmpty())
        }.body()
    }

    suspend fun discoverSources(request: SourceDiscoverRequestDto): List<SourceDiscoveryResultDto> {
        return client.post("$BASE_SOURCES_PATH/discover") {
            setBody(request)
        }.body()
    }

    suspend fun getFeedSourceSubscriptions(): List<SubscriptionResponseDto> {
        return client.get("$BASE_ME_PATH/$SUBSCRIPTIONS_PATH")
            .body()
    }

    suspend fun subscribeFeedSource(request: SubscriptionCreateRequestDto): SubscriptionResponseDto {
        return client.post("$BASE_ME_PATH/$SUBSCRIPTIONS_PATH") {
            setBody(request)
        }.body()
    }

    suspend fun unsubscribeFeedSource(sourceId: String): HttpStatusCode {
        return client.delete("$BASE_ME_PATH/$SUBSCRIPTIONS_PATH/$sourceId")
            .status
    }

    suspend fun getFeedSourceDetails(sourceId: String): SourceDetailsResponseDto {
        return client.get("$BASE_SOURCES_PATH/$sourceId")
            .body()
    }

}
