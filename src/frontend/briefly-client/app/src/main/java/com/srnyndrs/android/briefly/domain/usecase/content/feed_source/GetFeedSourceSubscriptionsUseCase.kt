package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetFeedSourceSubscriptionsUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(): Result<List<FeedSubscription>> {
        return repository.getFeedSourceSubscriptions()
    }
}
