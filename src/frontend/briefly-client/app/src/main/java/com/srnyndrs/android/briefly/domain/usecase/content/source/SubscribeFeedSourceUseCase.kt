package com.srnyndrs.android.briefly.domain.usecase.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.Subscription
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import javax.inject.Inject

class SubscribeFeedSourceUseCase @Inject constructor(
    private val repository: SourceRepository,
) {
    suspend operator fun invoke(sourceId: String): Result<Subscription> {
        return repository.subscribeFeedSource(sourceId)
    }
}
