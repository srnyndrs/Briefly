package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import androidx.paging.filter
import androidx.paging.map
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetExploreFeedUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@OptIn(ExperimentalTime::class, ExperimentalCoroutinesApi::class)
@HiltViewModel
class ExploreViewModel @Inject constructor(
    private val getExploreFeedUseCase: GetExploreFeedUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(ExploreState())
    val state = _state.asStateFlow()

    val posts: Flow<PagingData<ExploreArticle>> = state
        .map { it.filter }
        .distinctUntilChanged()
        .flatMapLatest { filter ->
            channelFlow {
                val exploreFeed = getExploreFeedUseCase(filter = filter)
                launch {
                    exploreFeed.metadata
                        .filterNotNull()
                        .collect { metadata ->
                            _state.update { current ->
                                if (current.filter == filter) {
                                    current.copy(
                                        filterOptions = metadata,
                                        filterOptionsFilter = filter,
                                    )
                                } else {
                                    current
                                }
                            }
                        }
                }
                exploreFeed.posts.collect { pagingData ->
                    val seenPostIds = mutableSetOf<String>()
                    send(
                        pagingData
                            .filter { post -> seenPostIds.add(element = post.id) }
                            .map { post ->
                                ExploreArticle(
                                    post = post,
                                    filter = filter,
                                )
                            },
                    )
                }
            }
        }
        .cachedIn(scope = viewModelScope)

    fun onEvent(event: ExploreEvent) {
        _state.update { current ->
            when (event) {
                is ExploreEvent.UpdateQuery -> current.copy(query = event.query)
                ExploreEvent.SubmitQuery -> {
                    val query = current.query.trim().ifBlank { null }
                    current.withFilter(
                        filter = current.filter.copy(
                            query = query,
                            sort = if (query != null) null else current.filter.sort ?: "freshness",
                        ),
                    )
                }
                ExploreEvent.ClearQuery -> current.withFilter(
                    filter = current.filter.copy(
                        query = null,
                        sort = current.filter.sort ?: "freshness",
                    ),
                ).copy(query = "")
                ExploreEvent.OpenFilterSheet -> current.copy(
                    isFilterSheetOpen = true,
                    draftFilter = current.filter,
                )
                ExploreEvent.DismissFilterSheet -> current.copy(isFilterSheetOpen = false)
                is ExploreEvent.UpdateDraftFilter -> current.copy(draftFilter = event.filter)
                ExploreEvent.ApplyDraftFilter -> current.withFilter(
                    filter = current.draftFilter.copy(
                        query = current.filter.query,
                        sort = if (current.filter.query != null) null else current.draftFilter.sort,
                    ),
                ).copy(isFilterSheetOpen = false)
                ExploreEvent.ResetDraftFilters -> current.copy(
                    draftFilter = ExplorePostFilter(
                        query = current.filter.query,
                        sort = if (current.filter.query == null) "freshness" else null,
                    ),
                )
                is ExploreEvent.RemoveCategory -> current.withFilter(
                    filter = current.filter.copy(
                        categories = current.filter.categories?.filter { it != event.category }?.ifEmpty { null },
                    ),
                )
                is ExploreEvent.RemoveLanguage -> current.withFilter(
                    filter = current.filter.copy(
                        languages = current.filter.languages?.filter { it != event.language }?.ifEmpty { null },
                    ),
                )
                is ExploreEvent.RemoveSource -> current.withFilter(
                    filter = current.filter.copy(
                        sourceIds = current.filter.sourceIds?.filter { it != event.sourceId }?.ifEmpty { null },
                    ),
                )
                ExploreEvent.ClearDateRange -> current.withFilter(
                    filter = current.filter.copy(
                        publishedFrom = null,
                        publishedTo = null,
                    ),
                )
                is ExploreEvent.ChangeSort -> current.withFilter(
                    filter = current.filter.copy(sort = if (current.filter.query == null) event.sort else null),
                )
                ExploreEvent.ClearAllFilters -> current.withFilter(
                    filter = ExplorePostFilter(
                        query = current.filter.query,
                        sort = if (current.filter.query == null) "freshness" else null,
                    ),
                )
            }
        }
    }

    private fun ExploreState.withFilter(filter: ExplorePostFilter) = copy(
        filter = filter,
        draftFilter = filter,
    )
}
