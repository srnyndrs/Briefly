package com.srnyndrs.android.briefly.ui.screen.main.navigation

sealed class MainRoutes(
    val route: String,
    //val iconDrawable: Int,
) {

    companion object {
        const val ARTICLE_ID_ARG = "postId"
        const val FEED_SOURCE_ID_ARG = "sourceId"
    }

    object Home: MainRoutes("home")
    object Explore: MainRoutes("explore")
    object FeedSources: MainRoutes("feed-sources")
    object Settings: MainRoutes("settings")
    object PostDetails: MainRoutes("posts/{$ARTICLE_ID_ARG}") {
        fun createRoute(postId: String) = "posts/$postId"
    }
    object SourceDetails: MainRoutes("sources/{$FEED_SOURCE_ID_ARG}") {
        fun createRoute(sourceId: String) = "sources/$sourceId"
    }
}
