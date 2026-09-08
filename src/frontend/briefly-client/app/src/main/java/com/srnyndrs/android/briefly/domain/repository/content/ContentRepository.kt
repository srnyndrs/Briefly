package com.srnyndrs.android.briefly.domain.repository.content

import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription
import androidx.paging.PagingData
import kotlinx.coroutines.flow.Flow

interface ContentRepository {
    fun getArticlePagingFlow(sourceIds: List<String>? = null): Flow<PagingData<ArticleItem>>
    suspend fun fetchArticles(page: Int? = 1, pageSize: Int? = 20, sourceIds: List<String>? = null): Result<ArticlePagingResult>
    suspend fun fetchFeedSources(query: String? = null): Result<List<FeedSourceResultItem>>
    suspend fun getFeedSourceSubscriptions(): Result<List<FeedSubscription>>
    suspend fun getFeedSourceDetails(sourceId: String): Result<FeedSourceDetails>
    suspend fun subscribeFeedSource(sourceId: String): Result<FeedSubscription>
    suspend fun unsubscribeFeedSource(sourceId: String): Result<String>
    suspend fun getArticleById(articleId: String): Result<ArticleDetails>
}
