package com.srnyndrs.android.briefly.ui.navigation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.navigation
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthScreen
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthViewModel
import com.srnyndrs.android.briefly.ui.screen.content.screen.ContentScreen
import com.srnyndrs.android.briefly.ui.screen.content.screen.ContentViewModel

@Composable
fun AppNavigation(
    modifier: Modifier = Modifier,
    navController: NavHostController
) {
    NavHost(
        modifier = Modifier.then(modifier),
        navController = navController,
        startDestination = Graph.Auth
    ) {
        authGraph(navController)
        mainGraph(navController)
        profileGraph(navController)
    }
}

fun NavGraphBuilder.authGraph(navController: NavHostController) {
    navigation<Graph.Auth>(
        startDestination = Screen.Auth
    ) {
        composable<Screen.Auth> {
            val viewModel: AuthViewModel = hiltViewModel()
            val state by viewModel.state.collectAsStateWithLifecycle()
            AuthScreen(
                state = state,
                onSuccess = {
                    navController.navigate(Graph.Main) {
                        popUpTo(Graph.Auth) { inclusive = true }
                    }
                },
                onEvent = viewModel::onEvent
            )
        }
    }
}

fun NavGraphBuilder.mainGraph(navController: NavHostController) {
    navigation<Graph.Main>(
        startDestination = Screen.Content
    ) {
        composable<Screen.Content> {
            val viewModel = hiltViewModel<ContentViewModel>()

            ContentScreen(
                onLogout = {
                    viewModel.logoutUser {
                        navController.navigate(Graph.Auth) {
                            popUpTo(Graph.Main) { inclusive = true }
                        }
                    }
                },
                onNavigateProfile = {
                    navController.navigate(Graph.Profile)
                }
            )
        }
    }
}

fun NavGraphBuilder.profileGraph(navController: NavHostController) {
    navigation<Graph.Profile>(
        startDestination = Screen.Profile
    ) {
        composable<Screen.Profile> {
            // TODO: implement ProfileScreen
            Column(
                modifier = Modifier.fillMaxSize(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Profile Screen"
                )
            }
        }
    }
}
