package com.srnyndrs.android.briefly.domain.usecase.content.article

import javax.inject.Inject

class AllArticleUseCase @Inject constructor(
    val getArticleByIdUseCase: GetArticleByIdUseCase,
    val getArticlePagingFlowUseCase: GetArticlePagingFlowUseCase,
    val getArticlesUseCase: GetArticlesUseCase,
)
