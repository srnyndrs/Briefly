package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.post.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.FilterSource
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
fun PostSummaryResponseDto.toDomain(): Post {
    return Post(
        id = postId,
        title = title,
        url = canonicalUrl,
        description = description,
        sourceTitle = sourceTitle,
        categories = categories.orEmpty().map { rawCategory ->
            Category.valueOf(rawCategory.uppercase())
        },
        imageUrl = imageRef,
        publishedAt = publishedAt,
        hasContent = hasContent,
    )
}

@OptIn(ExperimentalTime::class)
fun PostResponseDto.toDomain(): PostDetails {
    return PostDetails(
        id = postId,
        sourceId = sourceId,
        title = title,
        content = content,
        author = author,
        keywords = keywords,
        imageUrl = imageRef,
        categories = categories.orEmpty().map { rawCategory ->
            Category.valueOf(rawCategory.uppercase())
        },
        url = canonicalUrl,
        publishedAt = publishedAt,
        language = language,
        sourceTitle = sourceTitle,
    )
}

fun SourceEntry.toDomain(): FilterSource {
    return FilterSource(
        id = id,
        title = title,
    )
}

fun FilterOptionsDto.toDomain(): ExploreFilterOptions {
    return ExploreFilterOptions(
        categories = categories,
        languages = languages,
        authors = authors,
        keywords = keywords,
        sources = sources.map { source ->
            source.toDomain()
        },
    )
}
