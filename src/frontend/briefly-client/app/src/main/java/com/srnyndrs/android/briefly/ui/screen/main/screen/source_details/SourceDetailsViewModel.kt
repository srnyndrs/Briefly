package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticlesUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.AllFeedSourceUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetProfileUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.SetSourceBlockedUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlin.time.ExperimentalTime

@HiltViewModel(assistedFactory = SourceDetailsViewModel.SourceDetailsViewModelFactory::class)
class SourceDetailsViewModel @AssistedInject constructor(
    @Assisted private val sourceId: String,
    private val feedSourceUseCases: AllFeedSourceUseCase,
    private val getArticlesUseCase: GetArticlesUseCase,
    private val getProfileUseCase: GetProfileUseCase,
    private val setSourceBlockedUseCase: SetSourceBlockedUseCase,
): ViewModel() {

    @AssistedFactory
    interface SourceDetailsViewModelFactory {
        fun create(sourceId: String): SourceDetailsViewModel
    }

    private val _state = MutableStateFlow(SourceDetailsState())
    val state = _state.asStateFlow()

    init {
        fetchBlockStatus()
        fetchSourceDetails()
        fetchFeedArticles()
    }

    fun onEvent(event: SourceDetailsEvent) {
        when(event) {
            SourceDetailsEvent.RetryBlockStatus -> {
                if (_state.value.blockStatus is UiState.Error) fetchBlockStatus()
            }
            SourceDetailsEvent.ToggleBlock -> changeBlockState()
            SourceDetailsEvent.RetryFeedDetails -> {
                if (_state.value.feedDetails is UiState.Error) fetchSourceDetails()
            }
            SourceDetailsEvent.RetryArticles -> {
                if (_state.value.articles is UiState.Error) fetchFeedArticles()
            }
            is SourceDetailsEvent.ToggleFollow -> {
                val isFollowed = event.followed
                changeFollowState(!isFollowed)
            }
            is SourceDetailsEvent.ToggleSubscribe -> {
                val isSubscribed = event.subscribed
                changeSubscription(!isSubscribed)
            }
        }
    }

    private fun fetchBlockStatus() = viewModelScope.launch {
        _state.value = _state.value.copy(blockStatus = UiState.Loading)
        getProfileUseCase().fold(
            onSuccess = { profile ->
                _state.value = _state.value.copy(
                    blockStatus = UiState.Success(sourceId in profile.preferences.blockedSourceIds),
                )
            },
            onFailure = {
                _state.value = _state.value.copy(blockStatus = UiState.Error("Unable to load block status"))
            },
        )
    }

    private fun changeBlockState() {
        val blocked = (_state.value.blockStatus as? UiState.Success)?.data ?: return
        if (_state.value.isUpdatingBlock) return
        _state.value = _state.value.copy(isUpdatingBlock = true, blockUpdateFailed = false)
        viewModelScope.launch {
            setSourceBlockedUseCase(
                sourceId = sourceId,
                blocked = !blocked,
            ).fold(
                onSuccess = { preferences ->
                    _state.value = _state.value.copy(
                        blockStatus = UiState.Success(sourceId in preferences.blockedSourceIds),
                        isUpdatingBlock = false,
                    )
                },
                onFailure = {
                    _state.value = _state.value.copy(
                        isUpdatingBlock = false,
                        blockUpdateFailed = true,
                    )
                },
            )
        }
    }

    private fun fetchSourceDetails() = viewModelScope.launch {
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
        getArticlesUseCase(
            sourceIds = listOf(sourceId),
            applyUserPreferences = false,
        ).fold(
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
