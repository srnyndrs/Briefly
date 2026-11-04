package com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.source.exceptions.SourceAlreadyExistsException
import com.srnyndrs.android.briefly.domain.usecase.content.source.CreateFeedSourceUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.source.DiscoverFeedSourcesUseCase
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
    private val discoverFeedSourcesUseCase: DiscoverFeedSourcesUseCase,
    private val createFeedSourceUseCase: CreateFeedSourceUseCase,
    private val getFeedSourcesUseCase: GetFeedSourcesUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(value = FeedSourcesState())
    val state = _state.asStateFlow()

    private var discoveryUrl: String = ""
    private var discoveryJob: Job? = null

    private fun discover(url: String) {
        if (url.isBlank()) return
        discoveryJob?.cancel()
        val retained = (_state.value.discovery.results as? UiState.Success)
            ?.takeIf { url == discoveryUrl }
        discoveryUrl = url
        _state.update {
            it.copy(discovery = it.discovery.copy(
                results = retained ?: UiState.Loading,
                isRefreshing = retained != null,
                refreshFailed = false,
            ))
        }
        discoveryJob = viewModelScope.launch {
            val result = discoverFeedSourcesUseCase(url = url)
            currentCoroutineContext().ensureActive()
            _state.update {
                it.copy(discovery = it.discovery.copy(
                    results = result.fold(
                        onSuccess = { data -> UiState.Success(data = data.distinctBy { candidate -> candidate.url }) },
                        onFailure = { retained ?: UiState.Error(message = "") },
                    ),
                    isRefreshing = false,
                    refreshFailed = result.isFailure && retained != null,
                ))
            }
        }
    }

    private fun addSource(url: String) {
        val discovery = _state.value.discovery
        val addition = discovery.additions[url]
        if (addition is UiState.Loading || addition is UiState.Success) return
        val candidate = discovery.selectedSource?.takeIf { it.url == url } ?: return
        if (candidate.title.isBlank() || candidate.title.length > 255) return
        _state.update {
            it.copy(discovery = it.discovery.copy(
                additions = it.discovery.additions + (url to UiState.Loading),
                duplicateUrls = it.discovery.duplicateUrls - url,
            ))
        }
        viewModelScope.launch {
            val result = createFeedSourceUseCase(source = candidate)
            _state.update {
                it.copy(discovery = it.discovery.copy(
                    selectedSource = if (result.isSuccess && it.discovery.selectedSource?.url == url) {
                        null
                    } else it.discovery.selectedSource,
                    additions = it.discovery.additions + (url to result.fold(
                        onSuccess = { source -> UiState.Success(data = source.id) },
                        onFailure = { UiState.Error(message = "") },
                    )),
                    duplicateUrls = if (result.exceptionOrNull() is SourceAlreadyExistsException) {
                        it.discovery.duplicateUrls + url
                    } else it.discovery.duplicateUrls,
                ))
            }
            if (result.isSuccess) getFeedSources(query = currentQuery)
        }
    }

    private var currentQuery: String? = null
    private var searchJob: Job? = null

    init {
        getFeedSources()
    }

    fun onEvent(event: FeedSourcesEvent) {
        when (event) {
            is FeedSourcesEvent.SelectDiscoverySource -> _state.update {
                val source = (it.discovery.results as? UiState.Success)?.data
                    ?.firstOrNull { candidate -> candidate.url == event.url }
                it.copy(discovery = it.discovery.copy(selectedSource = source))
            }
            is FeedSourcesEvent.UpdateDiscoverySource -> _state.update {
                val source = it.discovery.selectedSource
                if (source?.url != event.source.url || it.discovery.additions[source.url] is UiState.Loading) it
                else it.copy(discovery = it.discovery.copy(selectedSource = source.copy(
                    title = event.source.title,
                    description = event.source.description,
                    siteName = event.source.siteName,
                )))
            }
            FeedSourcesEvent.DismissDiscoverySource -> _state.update {
                it.copy(discovery = it.discovery.copy(selectedSource = null))
            }
            is FeedSourcesEvent.UpdateDiscoveryUrl -> _state.update {
                it.copy(discovery = it.discovery.copy(url = event.url))
            }
            FeedSourcesEvent.Discover -> discover(url = _state.value.discovery.url.trim())
            FeedSourcesEvent.RetryDiscovery -> discover(url = discoveryUrl)
            is FeedSourcesEvent.AddSource -> addSource(url = event.url)
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
