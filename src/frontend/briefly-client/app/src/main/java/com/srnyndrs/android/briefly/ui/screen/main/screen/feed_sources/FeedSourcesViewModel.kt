package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.AllFeedSourceUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class FeedSourcesViewModel @Inject constructor(
    private val allFeedSourceUseCase: AllFeedSourceUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(FeedSourcesState())
    val state = _state.asStateFlow()
        .onStart {
            getFeedSources()
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5_000),
            FeedSourcesState()
        )

    private val queryState = MutableStateFlow<String?>(null)

    fun onEvent(event: FeedSourcesEvent) {
        when(event) {
            is FeedSourcesEvent.SearchFeedSource -> {
                val query = event.query
                getFeedSources(query)
            }
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

    private fun getFeedSources(query: String? = null) = viewModelScope.launch {
        _state.value = _state.value.copy(results = UiState.Loading)
        queryState.value = query
        allFeedSourceUseCase.getFeedSourcesUseCase(query).fold(
            onSuccess = { results ->
                _state.value = _state.value.copy(
                    results = UiState.Success(data = results)
                )
            },
            onFailure = { exception ->
                _state.value = _state.value.copy(
                    results = UiState.Error(message = exception.message ?: "Unknown error")
                )
            }
        )
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
                getFeedSources(queryState.value)
            },
            onFailure = {

            }
        )
    }

    private fun unsubscribeFeedSource(sourceId: String) = viewModelScope.launch {
        allFeedSourceUseCase.unsubscribeFeedSourceUseCase(sourceId).fold(
            onSuccess = { sourceId ->
                getFeedSources(queryState.value)
            },
            onFailure = {

            }
        )
    }

}
