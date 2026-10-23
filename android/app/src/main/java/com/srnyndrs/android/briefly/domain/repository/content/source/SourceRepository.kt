package com.srnyndrs.android.briefly.domain.repository.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.model.content.source.Subscription

interface SourceRepository {
    suspend fun fetchFeedSources(query: String? = null): Result<List<Source>>
    suspend fun getFeedSourceSubscriptions(): Result<List<Subscription>>
    suspend fun discoverFeedSources(url: String): Result<List<SourceDiscoveryResult>>
    suspend fun getFeedSourceDetails(sourceId: String): Result<SourceDetails>
    suspend fun subscribeFeedSource(sourceId: String): Result<Subscription>
    suspend fun unsubscribeFeedSource(sourceId: String): Result<String>
}
