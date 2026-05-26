package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class ExploreFeedSourcesUseCase @Inject constructor(
    private val contentRepository: ContentRepository
) {
    suspend operator fun invoke(url: String): Result<List<FeedSourceResultItem>> {
        return contentRepository.exploreFeedSources(url)
    }
}