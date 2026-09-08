package com.srnyndrs.android.briefly.ui.screen.content.navigation

sealed class ContentScreens(
    val route: String,
    //val iconDrawable: Int,
) {

    companion object {
        const val ARTICLE_ID_ARG = "postId"
        const val FEED_SOURCE_ID_ARG = "sourceId"
    }

    object Explore: ContentScreens("content_explore")
    object FeedSearch: ContentScreens("feed_search")
    object PostDetails: ContentScreens("article_details/{$ARTICLE_ID_ARG}") {
        fun createRoute(postId: String) = "article_details/$postId"
    }
    object SourceDetails: ContentScreens("feed_source_details/{$FEED_SOURCE_ID_ARG}") {
        fun createRoute(sourceId: String) = "feed_source_details/$sourceId"
    }


}
