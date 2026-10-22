package com.srnyndrs.android.briefly.data.repository.content.source

import com.srnyndrs.android.briefly.data.remote.content.source.SourceApiService
import com.srnyndrs.android.briefly.data.remote.content.source.SourceDiscoverRequestDto
import com.srnyndrs.android.briefly.data.remote.content.source.SubscriptionCreateRequestDto
import com.srnyndrs.android.briefly.data.remote.content.source.toDomain
import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.model.content.source.Subscription
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import io.ktor.http.HttpStatusCode
import javax.inject.Inject
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.CancellationException

@OptIn(ExperimentalTime::class)
class SourceRepositoryImpl @Inject constructor(
    private val sourceApiService: SourceApiService,
) : SourceRepository {

    override suspend fun fetchFeedSources(query: String?): Result<List<Source>> {
        return try {
            val response = sourceApiService.getFeedSources(query)
            val result = response.map { it.toDomain() }

            Result.success(value = result)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun getFeedSourceSubscriptions(): Result<List<Subscription>> {
        return try {
            val response = sourceApiService.getFeedSourceSubscriptions()
            val result = response.map { it.toDomain() }

            Result.success(value = result)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun discoverFeedSources(url: String): Result<List<SourceDiscoveryResult>> {
        return try {
            val response = sourceApiService.discoverSources(request = SourceDiscoverRequestDto(url))
            val result = response.map { it.toDomain() }

            Result.success(value = result)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun getFeedSourceDetails(sourceId: String): Result<SourceDetails> {
        return try {
            val response = sourceApiService.getFeedSourceDetails(sourceId)
            val result = response.toDomain()

            Result.success(value = result)
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun subscribeFeedSource(sourceId: String): Result<Subscription> {
        return try {
            val request = SubscriptionCreateRequestDto(sourceId)
            val response = sourceApiService.subscribeFeedSource(request)

            Result.success(value = response.toDomain())
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

    override suspend fun unsubscribeFeedSource(sourceId: String): Result<String> {
        return try {
            when (val response = sourceApiService.unsubscribeFeedSource(sourceId)) {
                HttpStatusCode.NoContent -> {
                    Result.success(value = sourceId)
                }
                else -> {
                    val exception = Exception(response.description)
                    Result.failure(exception = exception)
                }
            }
        } catch (exception: CancellationException) {
            throw exception
        } catch (exception: Exception) {
            Result.failure(exception = exception)
        }
    }

}
