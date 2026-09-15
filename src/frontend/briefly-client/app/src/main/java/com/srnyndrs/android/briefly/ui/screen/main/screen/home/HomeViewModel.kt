package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.filter.HomePostFilter
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetHomeFeedUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getHomeFeedUseCase: GetHomeFeedUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(HomeState())
    val state = _state.asStateFlow()

    val articles: Flow<PagingData<Post>> = state
        .map { HomePostFilter(category = it.selectedCategory) }
        .distinctUntilChanged()
        .flatMapLatest { filter ->
            channelFlow {
                val homeFeed = getHomeFeedUseCase(filter)
                launch {
                    homeFeed.metadata
                        .filterNotNull()
                        .collect { metadata ->
                            _state.update { current ->
                                if (current.selectedCategory == filter.category) {
                                    current.copy(
                                        headlines = metadata.headlines,
                                        categories = metadata.categories,
                                        selectedCategory = current.selectedCategory
                                            ?.takeIf {
                                                it in metadata.categories
                                            },
                                    )
                                } else {
                                    current
                                }
                            }
                        }
                }
                homeFeed.posts.collect { send(it) }
            }
        }
        .cachedIn(viewModelScope)

    fun onEvent(event: HomeEvent) {
        when (event) {
            is HomeEvent.SelectCategory -> _state.update {
                it.copy(selectedCategory = event.category)
            }
        }
    }
}
