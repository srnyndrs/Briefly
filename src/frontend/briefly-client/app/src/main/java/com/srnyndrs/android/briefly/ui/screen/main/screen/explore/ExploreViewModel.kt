package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.srnyndrs.android.briefly.domain.model.content.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetExplorePostPagingFlowUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
@HiltViewModel
class ExploreViewModel @Inject constructor(
    private val getExplorePostPagingFlowUseCase: GetExplorePostPagingFlowUseCase,
): ViewModel() {
    private val _filter = MutableStateFlow(ExplorePostFilter(sort = "newest"))
    val filter = _filter.asStateFlow()

    val posts: Flow<PagingData<Post>> = _filter
        .flatMapLatest(getExplorePostPagingFlowUseCase::invoke)
        .cachedIn(viewModelScope)

    fun onEvent(event: ExploreEvent) {
        when (event) {
            is ExploreEvent.UpdateQuery -> Unit
            is ExploreEvent.SubmitQuery -> _filter.value = _filter.value.copy(query = event.query.trim().ifBlank { null })
            is ExploreEvent.ChangeSort -> _filter.value = _filter.value.copy(sort = event.sort)
            ExploreEvent.ClearFilters -> _filter.value = ExplorePostFilter(sort = "newest")
        }
    }
}
