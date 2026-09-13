package com.srnyndrs.android.briefly.domain.usecase.content.article

import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetExplorePostPagingFlowUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetHomePostPagingFlowUseCase
import javax.inject.Inject

class AllArticleUseCase @Inject constructor(
    val getArticleByIdUseCase: GetArticleByIdUseCase,
    val getHomePostPagingFlowUseCase: GetHomePostPagingFlowUseCase,
    val getExplorePostPagingFlowUseCase: GetExplorePostPagingFlowUseCase,
    val getArticlesUseCase: GetArticlesUseCase,
)
