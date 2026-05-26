package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticlesUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.AllFeedSourceUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlin.time.ExperimentalTime

@HiltViewModel(assistedFactory = FeedDetailsViewModel.FeedDetailsViewModelFactory::class)
class FeedDetailsViewModel @AssistedInject constructor(
    @Assisted private val sourceId: String,
    private val feedSourceUseCases: AllFeedSourceUseCase,
    private val getArticlesUseCase: GetArticlesUseCase,
): ViewModel() {

    @AssistedFactory
    interface FeedDetailsViewModelFactory {
        fun create(sourceId: String): FeedDetailsViewModel
    }

    private val _state = MutableStateFlow(FeedDetailsState())
    val state = _state.asStateFlow()
        .onStart {
            fetchFeedDetails()
            fetchFeedArticles()
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5_000),
            FeedDetailsState()
        )

    fun onEvent(event: FeedDetailsEvent) {
        when(event) {
            is FeedDetailsEvent.ToggleFollow -> {
                val isFollowed = event.followed
                changeFollowState(!isFollowed)
            }
            is FeedDetailsEvent.ToggleSubscribe -> {
                val isSubscribed = event.subscribed
                changeSubscription(!isSubscribed)
            }
        }
    }

    private fun fetchFeedDetails() = viewModelScope.launch {
        _state.value = _state.value.copy(
            feedDetails = UiState.Loading
        )
        feedSourceUseCases.getFeedSourceDetailsUseCase(sourceId).fold(
            onSuccess = { data ->
                _state.value = _state.value.copy(
                    feedDetails = UiState.Success(data)
                )
            },
            onFailure = { exception ->
                _state.value = _state.value.copy(
                    feedDetails = UiState.Error(exception.message ?: "Unknown error occurred")
                )
            }
        )
    }

    private fun fetchFeedArticles() = viewModelScope.launch {
        _state.value = _state.value.copy(
            articles = UiState.Loading
        )
        getArticlesUseCase(sourceIds = listOf(sourceId)).fold(
            onSuccess = { (_, _, items) ->
                _state.value = _state.value.copy(
                    articles = UiState.Success(items)
                )
            },
            onFailure = { exception ->
                _state.value = _state.value.copy(
                    articles = UiState.Error(exception.message ?: "Unknown error occurred")
                )
            }
        )
    }

    @OptIn(ExperimentalTime::class)
    private fun changeSubscription(newValue: Boolean) = viewModelScope.launch {
        val feedDetails = (_state.value.feedDetails as UiState.Success).data
        if(newValue) {
            feedSourceUseCases.subscribeFeedSourceUseCase(sourceId).fold(
                onSuccess = {
                    _state.value = _state.value.copy(
                        feedDetails = UiState.Success(
                            data = feedDetails.copy(
                                subscribed = true
                            )
                        )
                    )
                },
                onFailure = {}
            )
        } else {
            feedSourceUseCases.unsubscribeFeedSourceUseCase(sourceId).fold(
                onSuccess = {
                    _state.value = _state.value.copy(
                        feedDetails = UiState.Success(
                            data = feedDetails.copy(
                                subscribed = false
                            )
                        )
                    )
                },
                onFailure = {}
            )
        }
    }

    @OptIn(ExperimentalTime::class)
    private fun changeFollowState(newValue: Boolean) = viewModelScope.launch {
        val feedDetails = (_state.value.feedDetails as UiState.Success).data
        _state.value = _state.value.copy(
            feedDetails = UiState.Success(
                data = feedDetails.copy(
                    followed = newValue
                )
            )
        )
    }

}
