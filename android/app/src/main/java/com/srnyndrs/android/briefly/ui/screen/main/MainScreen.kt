package com.srnyndrs.android.briefly.ui.screen.main

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.Scaffold
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationGraph
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainRoutes
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.launch

@Composable
fun MainScreen(
    modifier: Modifier = Modifier,
    state: MainState,
    onMainEvent: (MainEvent) -> Unit,
) {

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    val showTopBar = currentRoute != MainRoutes.PostDetails.route &&
        currentRoute != MainRoutes.SourceDetails.route

    val navigateToRoute = { route: String ->
        navController.navigate(route = route) {
            launchSingleTop = true
            restoreState = true
            popUpTo(id = navController.graph.startDestinationId) {
                saveState = true
            }
        }
        scope.launch { drawerState.close() }
    }

    ModalNavigationDrawer(
        modifier = Modifier.then(modifier),
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet(
                modifier = Modifier.widthIn(max = 320.dp),
                drawerContainerColor = MaterialTheme.colorScheme.surface,
                drawerContentColor = MaterialTheme.colorScheme.onSurface,
            ) {
                MainDrawerContent(
                    modifier = Modifier.fillMaxWidth(),
                    currentRoute = currentRoute,
                    isSigningOut = state.isSigningOut,
                    onDrawerEvent = { event ->
                        when (event) {
                            MainDrawerContentEvent.NavigateHomeScreen -> navigateToRoute(MainRoutes.Home.route)
                            MainDrawerContentEvent.NavigateExploreScreen -> navigateToRoute(MainRoutes.Explore.route)
                            MainDrawerContentEvent.NavigateFeedsScreen -> navigateToRoute(MainRoutes.FeedSources.route)
                            MainDrawerContentEvent.NavigateSettingsScreen -> navigateToRoute(MainRoutes.Settings.route)
                            MainDrawerContentEvent.SignOutUser -> onMainEvent(MainEvent.SignOut)
                        }
                    },
                )
            }
        },
    ) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = {
                AnimatedVisibility(visible = showTopBar) {
                    TopAppBar(
                        modifier = Modifier.fillMaxWidth(),
                        onMenuSelect = { scope.launch { drawerState.open() } },
                    )
                }
            },
        ) { innerPadding ->
            MainNavigationGraph(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(top = if (showTopBar) innerPadding.calculateTopPadding() else 0.dp),
                navController = navController,
            )
        }
    }
}

@PreviewLightDark
@Composable
fun MainScreenPreview() {
    BrieflyTheme {
        MainScreen(
            modifier = Modifier.fillMaxSize(),
            state = MainState(),
            onMainEvent = {},
        )
    }
}
