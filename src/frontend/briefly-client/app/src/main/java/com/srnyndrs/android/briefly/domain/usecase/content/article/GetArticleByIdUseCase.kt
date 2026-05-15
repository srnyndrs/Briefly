package com.srnyndrs.android.briefly.domain.usecase.content.article

import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetArticleByIdUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(articleId: String): Result<ArticleDetails> {
        return repository.getArticleById(articleId)
    }
}