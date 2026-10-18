package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.AllFeedSourceUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class FeedSourcesViewModel @Inject constructor(
    private val allFeedSourceUseCase: AllFeedSourceUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(FeedSourcesState())
    val state = _state.asStateFlow()

    private var currentQuery: String? = null
    private var searchJob: Job? = null

    init {
        getFeedSources()
    }

    fun onEvent(event: FeedSourcesEvent) {
        when(event) {
            is FeedSourcesEvent.SearchFeedSource -> {
                val query = event.query
                getFeedSources(query)
            }
            FeedSourcesEvent.RetrySearch -> getFeedSources(currentQuery)
            is FeedSourcesEvent.DiscoverFeedSource -> {
                val url = event.url
                discoverFeedSources(url)
            }
            is FeedSourcesEvent.SubscribeFeedSource -> {
                val sourceId = event.sourceId
                subscribeFeedSource(sourceId)
            }
            is FeedSourcesEvent.UnsubscribeFeedSource -> {
                val sourceId = event.sourceId
                unsubscribeFeedSource(sourceId)
            }
        }
    }

    private fun getFeedSources(query: String? = null) {
        searchJob?.cancel()
        val retainedResults = (_state.value.results as? UiState.Success)
            ?.takeIf { query == currentQuery }
        currentQuery = query
        _state.value = _state.value.copy(
            results = retainedResults ?: UiState.Loading,
            isRefreshing = retainedResults != null,
            refreshError = null,
        )
        searchJob = viewModelScope.launch {
            val result = allFeedSourceUseCase.getFeedSourcesUseCase(query)
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { results ->
                    _state.value = _state.value.copy(
                        results = UiState.Success(data = results),
                        isRefreshing = false,
                    )
                },
                onFailure = { exception ->
                    val message = exception.message ?: "Unknown error"
                    _state.value = _state.value.copy(
                        results = retainedResults ?: UiState.Error(message = message),
                        isRefreshing = false,
                        refreshError = message.takeIf { retainedResults != null },
                    )
                },
            )
        }
    }

    private fun discoverFeedSources(url: String) = viewModelScope.launch {
        allFeedSourceUseCase.discoverFeedSourceUseCase(url).fold(
            onSuccess = {

            },
            onFailure = {

            }
        )
    }

    private fun subscribeFeedSource(sourceId: String) = viewModelScope.launch {
        allFeedSourceUseCase.subscribeFeedSourceUseCase(sourceId).fold(
            onSuccess = {
                getFeedSources(currentQuery)
            },
            onFailure = {

            }
        )
    }

    private fun unsubscribeFeedSource(sourceId: String) = viewModelScope.launch {
        allFeedSourceUseCase.unsubscribeFeedSourceUseCase(sourceId).fold(
            onSuccess = { sourceId ->
                getFeedSources(currentQuery)
            },
            onFailure = {

            }
        )
    }

}
