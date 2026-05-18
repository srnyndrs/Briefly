package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class SubscribeFeedSourceUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(sourceId: String): Result<FeedSubscription> {
        return repository.subscribeFeedSource(sourceId)
    }
}
