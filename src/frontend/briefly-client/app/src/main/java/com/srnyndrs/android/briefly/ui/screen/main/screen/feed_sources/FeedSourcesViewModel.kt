package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.source.GetFeedSourcesUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class FeedSourcesViewModel @Inject constructor(
    private val getFeedSourcesUseCase: GetFeedSourcesUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(value = FeedSourcesState())
    val state = _state.asStateFlow()

    private var currentQuery: String? = null
    private var searchJob: Job? = null

    init {
        getFeedSources()
    }

    fun onEvent(event: FeedSourcesEvent) {
        when (event) {
            is FeedSourcesEvent.UpdateSearchText -> _state.update {
                it.copy(searchText = event.text)
            }
            FeedSourcesEvent.SearchFeedSource -> getFeedSources(query = _state.value.searchText)
            FeedSourcesEvent.RetrySearch -> getFeedSources(query = currentQuery)
        }
    }

    private fun getFeedSources(query: String? = null) {
        searchJob?.cancel()
        val retainedResults = (_state.value.results as? UiState.Success)
            ?.takeIf { query == currentQuery }
        currentQuery = query
        _state.update {
            it.copy(
                results = retainedResults ?: UiState.Loading,
                isRefreshing = retainedResults != null,
                refreshError = null,
            )
        }
        searchJob = viewModelScope.launch {
            val result = getFeedSourcesUseCase(query = query)
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { results ->
                    _state.update {
                        it.copy(
                            results = UiState.Success(data = results),
                            isRefreshing = false,
                        )
                    }
                },
                onFailure = { exception ->
                    // Retain diagnostics; the screen supplies localized failure text.
                    val message = exception.message.orEmpty()
                    _state.update {
                        it.copy(
                            results = retainedResults ?: UiState.Error(message = message),
                            isRefreshing = false,
                            refreshError = message.takeIf { retainedResults != null },
                        )
                    }
                },
            )
        }
    }
}
