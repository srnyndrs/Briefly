package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class UnsubscribeFeedSourceUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(sourceId: String): Result<String> {
        return repository.unsubscribeFeedSource(sourceId)
    }
}
