package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.ExploreFeedSourcesUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.GetFeedSourceSubscriptionsUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.GetFeedSourcesUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.SubscribeFeedSourceUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.UnsubscribeFeedSourceUseCase
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
class FeedSearchViewModel @Inject constructor(
    private val getFeedSourcesUseCase: GetFeedSourcesUseCase,
    private val subscribeFeedSourceUseCase: SubscribeFeedSourceUseCase,
    private val unsubscribeFeedSourceUseCase: UnsubscribeFeedSourceUseCase,
): ViewModel() {

    private val _state = MutableStateFlow<FeedSearchState>(FeedSearchState())
    val state = _state.asStateFlow()
        .onStart {
            getFeedSources()
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5_000),
            FeedSearchState()
        )

    private val queryState = MutableStateFlow<String?>(null)

    fun onEvent(event: FeedSearchEvent) {
        when(event) {
            is FeedSearchEvent.SearchFeedSource -> {
                val query = event.query
                getFeedSources(query)
            }
            is FeedSearchEvent.SubscribeFeedSource -> {
                val sourceId = event.sourceId
                subscribeFeedSource(sourceId)
            }
            is FeedSearchEvent.UnsubscribeFeedSource -> {
                val sourceId = event.sourceId
                unsubscribeFeedSource(sourceId)
            }
        }
    }

    private fun getFeedSources(query: String? = null) = viewModelScope.launch {
        _state.value = _state.value.copy(results = UiState.Loading)
        queryState.value = query
        getFeedSourcesUseCase(query).fold(
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

    private fun subscribeFeedSource(sourceId: String) = viewModelScope.launch {
        subscribeFeedSourceUseCase(sourceId).fold(
            onSuccess = {
                getFeedSources(queryState.value)
            },
            onFailure = {

            }
        )
    }

    private fun unsubscribeFeedSource(sourceId: String) = viewModelScope.launch {
        unsubscribeFeedSourceUseCase(sourceId).fold(
            onSuccess = { sourceId ->
                getFeedSources(queryState.value)
            },
            onFailure = {

            }
        )
    }

}
