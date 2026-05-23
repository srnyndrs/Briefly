package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import javax.inject.Inject

class AllFeedSourceUseCase  @Inject constructor(
    val exploreFeedSourcesUseCase: ExploreFeedSourcesUseCase,
    val getFeedSourceDetailsUseCase: GetFeedSourceDetailsUseCase,
    val getFeedSourceSubscriptionsUseCase: GetFeedSourceSubscriptionsUseCase,
    val getFeedSourceUseCase: GetFeedSourcesUseCase,
    val subscribeFeedSourceUseCase: SubscribeFeedSourceUseCase,
    val unsubscribeFeedSourceUseCase: UnsubscribeFeedSourceUseCase,
)