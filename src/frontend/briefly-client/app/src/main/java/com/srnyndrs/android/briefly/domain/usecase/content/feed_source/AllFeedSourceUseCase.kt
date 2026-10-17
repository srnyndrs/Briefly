package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import javax.inject.Inject

class AllFeedSourceUseCase @Inject constructor(
    val getFeedSourceDetailsUseCase: GetFeedSourceDetailsUseCase,
    val getFeedSourceSubscriptionsUseCase: GetFeedSourceSubscriptionsUseCase,
    val getFeedSourcesUseCase: GetFeedSourcesUseCase,
    val discoverFeedSourceUseCase: DiscoverFeedSourceUseCase,
    val subscribeFeedSourceUseCase: SubscribeFeedSourceUseCase,
    val unsubscribeFeedSourceUseCase: UnsubscribeFeedSourceUseCase,
)
