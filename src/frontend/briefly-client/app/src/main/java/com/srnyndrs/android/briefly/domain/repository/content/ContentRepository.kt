package com.srnyndrs.android.briefly.domain.repository.content

import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem

interface ContentRepository {
    suspend fun fetchArticles(limit: Long? = null, offset: Long? = null): Result<List<ArticleItem>>
    suspend fun exploreFeedSources(url: String): Result<List<FeedSourceResultItem>>
    suspend fun getArticleById(articleId: String): Result<ArticleDetails>
}
