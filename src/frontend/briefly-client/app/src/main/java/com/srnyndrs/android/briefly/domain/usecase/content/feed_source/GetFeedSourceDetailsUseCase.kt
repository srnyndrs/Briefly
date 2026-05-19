package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetFeedSourceDetailsUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(sourceId: String): Result<FeedSourceDetails> {
        return repository.getFeedSourceDetails(sourceId)
    }
}
