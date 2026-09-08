package com.srnyndrs.android.briefly.data.repository.content

import androidx.paging.PagingSource
import androidx.paging.PagingState
import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.toDomain
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem

class ArticlePagingSource(
    private val contentApiService: ContentApiService,
    private val sourceIds: List<String>? = null,
) : PagingSource<Int, ArticleItem>() {

    override fun getRefreshKey(state: PagingState<Int, ArticleItem>): Int? {
        return state.anchorPosition?.let { anchorPosition ->
            val anchorPage = state.closestPageToPosition(anchorPosition)
            anchorPage?.prevKey?.plus(1) ?: anchorPage?.nextKey?.minus(1)
        }
    }

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, ArticleItem> {
        val page = params.key ?: 1
        return try {
            val response = contentApiService.getFeed(
                page = page,
                pageSize = params.loadSize,
                sourceIds = sourceIds
            )
            val items = response.items.map { it.toDomain() }
            val prevKey = if (page <= 1) null else page - 1
            val nextKey = if (items.isEmpty() || page >= response.pageCount) null else page + 1

            LoadResult.Page(
                data = items,
                prevKey = prevKey,
                nextKey = nextKey
            )
        } catch (exception: Exception) {
            LoadResult.Error(exception)
        }
    }
}
