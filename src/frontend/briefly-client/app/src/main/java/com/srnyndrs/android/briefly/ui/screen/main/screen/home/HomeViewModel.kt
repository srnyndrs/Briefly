package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import androidx.paging.filter
import androidx.paging.map
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.HomePostFilter
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetHomeFeedUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getHomeFeedUseCase: GetHomeFeedUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(HomeState())
    val state = _state.asStateFlow()

    val articles: Flow<PagingData<HomeArticle>> = state
        .map { HomePostFilter(category = it.selectedCategory) }
        .distinctUntilChanged()
        .flatMapLatest { filter ->
            channelFlow {
                val homeFeed = getHomeFeedUseCase(filter = filter)
                launch {
                    homeFeed.metadata
                        .filterNotNull()
                        .collect { metadata ->
                            _state.update { current ->
                                if (current.selectedCategory == filter.category) {
                                    current.copy(
                                        headlines = if (current.categories == null) {
                                            metadata.headlines
                                        } else {
                                            current.headlines
                                        },
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
                homeFeed.posts.collect { pagingData ->
                    send(
                        element = pagingData.filter { post ->
                            // Paging starts loading before metadata can initialize the headlines.
                            val current = state.first { it.categories != null }
                            current.headlines.none { it.id == post.id }
                        }.map { post ->
                            HomeArticle(
                                post = post,
                                category = filter.category,
                            )
                        },
                    )
                }
            }
        }
        .cachedIn(scope = viewModelScope)

    fun onEvent(event: HomeEvent) {
        when (event) {
            is HomeEvent.SelectCategory -> _state.update {
                if (it.selectedCategory == event.category) it else it.copy(
                    selectedCategory = event.category,
                )
            }
        }
    }

}
