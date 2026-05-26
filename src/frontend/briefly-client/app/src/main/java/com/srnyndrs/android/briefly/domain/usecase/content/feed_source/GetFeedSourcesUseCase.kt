package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetFeedSourcesUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(query: String? = null): Result<List<FeedSourceResultItem>> {
        return repository.fetchFeedSources(query)
    }
}
