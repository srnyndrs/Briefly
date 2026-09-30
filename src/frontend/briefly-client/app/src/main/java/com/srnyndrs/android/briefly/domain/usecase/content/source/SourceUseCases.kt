package com.srnyndrs.android.briefly.domain.usecase.content.source

import javax.inject.Inject

class SourceUseCases @Inject constructor(
    val getFeedSourceDetailsUseCase: GetFeedSourceDetailsUseCase,
    val subscribeFeedSourceUseCase: SubscribeFeedSourceUseCase,
    val unsubscribeFeedSourceUseCase: UnsubscribeFeedSourceUseCase,
)
