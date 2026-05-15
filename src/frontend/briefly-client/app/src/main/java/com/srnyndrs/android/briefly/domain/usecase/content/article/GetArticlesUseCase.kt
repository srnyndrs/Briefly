package com.srnyndrs.android.briefly.domain.usecase.content.article

import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetArticlesUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(): Result<ArticlePagingResult> {
        repository.fetchArticles().fold(
            onSuccess = { items ->
                // TODO: actual paging result
                val result =  ArticlePagingResult(
                    page = 1,
                    count = 5,
                    items = items
                )

                return Result.success(result)
            },
            onFailure = { exception ->
                return Result.failure(exception)
            }
        )
    }
}
