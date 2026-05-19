package com.srnyndrs.android.briefly.domain.repository.content

import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription

interface ContentRepository {
    suspend fun fetchArticles(limit: Long? = null, offset: Long? = null): Result<List<ArticleItem>>
    suspend fun fetchFeedSources(query: String? = null): Result<List<FeedSourceResultItem>>
    suspend fun getFeedSourceSubscriptions(): Result<List<FeedSubscription>>
    suspend fun getFeedSourceDetails(sourceId: String): Result<FeedSourceDetails>
    suspend fun subscribeFeedSource(sourceId: String): Result<FeedSubscription>
    suspend fun unsubscribeFeedSource(sourceId: String): Result<String>
    suspend fun exploreFeedSources(url: String): Result<List<FeedSourceResultItem>>
    suspend fun getArticleById(articleId: String): Result<ArticleDetails>
}
