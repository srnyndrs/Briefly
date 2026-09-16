package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetExplorePostPagingFlowUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class, ExperimentalCoroutinesApi::class)
@HiltViewModel
class ExploreViewModel @Inject constructor(
    private val getExplorePostPagingFlowUseCase: GetExplorePostPagingFlowUseCase,
): ViewModel() {

    private val _state = MutableStateFlow(ExploreState())
    val state = _state.asStateFlow()

    val posts: Flow<PagingData<Post>> = state
        .map { it.filter }
        .distinctUntilChanged()
        .flatMapLatest { filter -> getExplorePostPagingFlowUseCase(filter) }
        .cachedIn(viewModelScope)

    fun onEvent(event: ExploreEvent) {
        when (event) {
            is ExploreEvent.UpdateQuery -> _state.update { it.copy(query = event.query) }
            ExploreEvent.SubmitQuery -> _state.update { state ->
                state.copy(
                    filter = state.filter.copy(
                        query = state.query.trim().ifBlank { null },
                    ),
                )
            }
            is ExploreEvent.ChangeSort -> _state.update { state ->
                state.copy(filter = state.filter.copy(sort = event.sort))
            }
            ExploreEvent.ClearFilters -> _state.value = ExploreState()
        }
    }
}
