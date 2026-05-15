package com.srnyndrs.android.briefly.ui.screen.content.navigation

sealed class ContentScreens(
    val route: String,
    //val iconDrawable: Int,
) {

    companion object {
        const val ARTICLE_ID_ARG = "articleId"
    }

    object Explore: ContentScreens("content_explore")
    object ArticleSearch: ContentScreens("article_search")
    object FeedSearch: ContentScreens("feed_search")
    object ArticleDetails: ContentScreens("article_details/{$ARTICLE_ID_ARG}") {
        fun createRoute(articleId: String) = "article_details/$articleId"
    }
}
