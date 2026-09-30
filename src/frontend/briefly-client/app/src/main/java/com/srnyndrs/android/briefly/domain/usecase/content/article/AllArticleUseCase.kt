package com.srnyndrs.android.briefly.domain.usecase.content.article

import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetExplorePostPagingFlowUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetHomeFeedUseCase
import javax.inject.Inject

class AllArticleUseCase @Inject constructor(
    val getArticleByIdUseCase: GetArticleByIdUseCase,
    val getHomeFeedUseCase: GetHomeFeedUseCase,
    val getExplorePostPagingFlowUseCase: GetExplorePostPagingFlowUseCase,
    val getArticlesUseCase: GetArticlesUseCase,
)
