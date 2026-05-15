package com.srnyndrs.android.briefly.ui.screen.content.navigation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.srnyndrs.android.briefly.ui.screen.content.screen.article_details.ArticleDetailsScreen
import com.srnyndrs.android.briefly.ui.screen.content.screen.article_details.ArticleDetailsViewModel
import com.srnyndrs.android.briefly.ui.screen.content.screen.article_search.ArticleSearch
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.ContentExploreScreen
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.ContentExploreViewModel
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search.FeedSearchScreen
import com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search.FeedSearchViewModel

@Composable
fun ContentNavigationGraph(
    modifier: Modifier = Modifier,
    navController: NavHostController,
) {
    NavHost(
        modifier = Modifier.then(modifier),
        navController = navController,
        startDestination = ContentScreens.Explore.route
    ) {
        composable(
            route = ContentScreens.Explore.route
        ) {

            val viewModel = hiltViewModel<ContentExploreViewModel>()
            val state by viewModel.state.collectAsStateWithLifecycle()

            ContentExploreScreen(
                modifier = Modifier.fillMaxSize(),
                state = state
            ) { articleId ->
                navController.navigate(ContentScreens.ArticleDetails.createRoute(articleId))
            }
        }
        composable(
            route = ContentScreens.FeedSearch.route
        ) {

            val viewModel = hiltViewModel<FeedSearchViewModel>()
            val state by viewModel.state.collectAsStateWithLifecycle()

            FeedSearchScreen(
                modifier = Modifier.fillMaxSize()
                    .padding(6.dp),
                state = state
            ) { url ->
                // TODO: refactor to events
                viewModel.exploreFeedSources(url)
            }
        }
        composable(
            route = ContentScreens.ArticleSearch.route
        ) {
            ArticleSearch(
                modifier = Modifier.fillMaxSize()
            )
        }
        composable(
            route = ContentScreens.ArticleDetails.route,
            arguments = listOf(
                navArgument(ContentScreens.ARTICLE_ID_ARG) { type = NavType.StringType },
            ),
        ) { entry ->

            val articleId = entry.arguments?.getString(ContentScreens.ARTICLE_ID_ARG)
            articleId?.let {
                val viewModel = hiltViewModel<ArticleDetailsViewModel, ArticleDetailsViewModel.Factory>(
                    creationCallback = { factory -> factory.create(articleId) }
                )

                val state by viewModel.state.collectAsStateWithLifecycle()

                ArticleDetailsScreen(
                    modifier = Modifier.fillMaxSize(),
                    state = state
                )
            } ?: Column {
                // TODO: handle null state
            }
        }
    }
}
