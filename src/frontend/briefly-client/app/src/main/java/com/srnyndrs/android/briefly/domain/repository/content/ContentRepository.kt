package com.srnyndrs.android.briefly.domain.repository.content

import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.ExploreFeed
import com.srnyndrs.android.briefly.domain.model.content.HomeFeed
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.Subscription
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.model.content.filter.HomePostFilter
import kotlinx.coroutines.flow.Flow

interface ContentRepository {
    fun getHomeFeed(filter: HomePostFilter): HomeFeed
    fun getExplorePostPagingFlow(filter: ExplorePostFilter): Flow<PagingData<Post>>
    fun getExploreFeed(filter: ExplorePostFilter): ExploreFeed
    suspend fun fetchArticles(page: Int? = 1, pageSize: Int? = 20, sourceIds: List<String>? = null): Result<PostPagingResult>
    suspend fun fetchFeedSources(query: String? = null): Result<List<Source>>
    suspend fun getFeedSourceSubscriptions(): Result<List<Subscription>>
    suspend fun getFeedSourceDetails(sourceId: String): Result<SourceDetails>
    suspend fun subscribeFeedSource(sourceId: String): Result<Subscription>
    suspend fun unsubscribeFeedSource(sourceId: String): Result<String>
    suspend fun getArticleById(postId: String): Result<PostDetails>
}
