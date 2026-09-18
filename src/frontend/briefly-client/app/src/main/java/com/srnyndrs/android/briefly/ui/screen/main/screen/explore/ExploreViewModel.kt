package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetExploreFeedUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
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
import javax.inject.Inject
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class, ExperimentalCoroutinesApi::class)
@HiltViewModel
class ExploreViewModel @Inject constructor(
    private val getExploreFeedUseCase: GetExploreFeedUseCase,
) : ViewModel() {

    private val _state = MutableStateFlow(ExploreState())
    val state = _state.asStateFlow()

    val posts: Flow<PagingData<Post>> = state
        .map { it.filter }
        .distinctUntilChanged()
        .flatMapLatest { filter ->
            channelFlow {
                val exploreFeed = getExploreFeedUseCase(filter)
                launch {
                    exploreFeed.metadata
                        .filterNotNull()
                        .collect { metadata ->
                            _state.update { current ->
                                current.copy(
                                    filterOptions = metadata,
                                )
                            }
                        }
                }
                exploreFeed.posts.collect { send(it) }
            }
        }
        .cachedIn(viewModelScope)

    fun onEvent(event: ExploreEvent) {
        when (event) {
            is ExploreEvent.UpdateQuery -> _state.update { it.copy(query = event.query) }
            ExploreEvent.SubmitQuery -> _state.update { current ->
                val normalizedQuery = current.query.trim().ifBlank { null }
                val updatedFilter = current.filter.copy(
                    query = normalizedQuery,
                    sort = if (normalizedQuery != null) null else (current.filter.sort ?: "freshness"),
                )
                current.copy(
                    filter = updatedFilter,
                    draftFilter = updatedFilter,
                )
            }
            ExploreEvent.ClearQuery -> _state.update { current ->
                val updatedFilter = current.filter.copy(
                    query = null,
                    sort = current.filter.sort ?: "freshness",
                )
                current.copy(
                    query = "",
                    filter = updatedFilter,
                    draftFilter = updatedFilter,
                )
            }
            ExploreEvent.OpenFilterSheet -> _state.update { current ->
                current.copy(
                    isFilterSheetOpen = true,
                    draftFilter = current.filter,
                )
            }
            ExploreEvent.DismissFilterSheet -> _state.update { it.copy(isFilterSheetOpen = false) }
            is ExploreEvent.UpdateDraftFilter -> _state.update { it.copy(draftFilter = event.filter) }
            ExploreEvent.ApplyDraftFilter -> _state.update { current ->
                current.copy(
                    filter = current.draftFilter,
                    isFilterSheetOpen = false,
                )
            }
            ExploreEvent.ResetDraftFilters -> _state.update { current ->
                current.copy(
                    draftFilter = ExplorePostFilter(
                        query = current.filter.query,
                        sort = if (current.filter.query.isNullOrBlank()) "freshness" else null,
                    )
                )
            }
            is ExploreEvent.RemoveCategory -> _state.update { current ->
                val newCategories = current.filter.categories?.filter { it != event.category }?.ifEmpty { null }
                val updatedFilter = current.filter.copy(categories = newCategories)
                current.copy(filter = updatedFilter, draftFilter = updatedFilter)
            }
            is ExploreEvent.RemoveLanguage -> _state.update { current ->
                val newLanguages = current.filter.languages?.filter { it != event.language }?.ifEmpty { null }
                val updatedFilter = current.filter.copy(languages = newLanguages)
                current.copy(filter = updatedFilter, draftFilter = updatedFilter)
            }
            is ExploreEvent.RemoveSource -> _state.update { current ->
                val newSources = current.filter.sourceIds?.filter { it != event.sourceId }?.ifEmpty { null }
                val updatedFilter = current.filter.copy(sourceIds = newSources)
                current.copy(filter = updatedFilter, draftFilter = updatedFilter)
            }
            ExploreEvent.ClearDateRange -> _state.update { current ->
                val updatedFilter = current.filter.copy(publishedFrom = null, publishedTo = null)
                current.copy(filter = updatedFilter, draftFilter = updatedFilter)
            }
            is ExploreEvent.ChangeSort -> _state.update { current ->
                val updatedFilter = current.filter.copy(sort = event.sort)
                current.copy(filter = updatedFilter, draftFilter = updatedFilter)
            }
            ExploreEvent.ClearAllFilters -> _state.update { current ->
                val updatedFilter = ExplorePostFilter(
                    query = current.filter.query,
                    sort = if (current.filter.query.isNullOrBlank()) "freshness" else null,
                )
                current.copy(
                    filter = updatedFilter,
                    draftFilter = updatedFilter,
                )
            }
        }
    }
}
