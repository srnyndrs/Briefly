package com.srnyndrs.android.briefly.domain.repository.content

import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.domain.model.content.Subscription
import androidx.paging.PagingData
import kotlinx.coroutines.flow.Flow

interface ContentRepository {
    fun getArticlePagingFlow(sourceIds: List<String>? = null): Flow<PagingData<Post>>
    suspend fun fetchArticles(page: Int? = 1, pageSize: Int? = 20, sourceIds: List<String>? = null): Result<PostPagingResult>
    suspend fun fetchFeedSources(query: String? = null): Result<List<Source>>
    suspend fun getFeedSourceSubscriptions(): Result<List<Subscription>>
    suspend fun getFeedSourceDetails(sourceId: String): Result<SourceDetails>
    suspend fun subscribeFeedSource(sourceId: String): Result<Subscription>
    suspend fun unsubscribeFeedSource(sourceId: String): Result<String>
    suspend fun getArticleById(postId: String): Result<PostDetails>
}
