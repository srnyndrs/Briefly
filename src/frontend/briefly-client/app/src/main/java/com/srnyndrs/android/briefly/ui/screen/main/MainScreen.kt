package com.srnyndrs.android.briefly.ui.screen.main

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.Scaffold
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.navigation.NavigationEvent
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainNavigationGraph
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainRoutes
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.launch

@Composable
fun MainScreen(
    modifier: Modifier = Modifier,
    onProfileNavigation: () -> Unit,
    onLogout: () -> Unit,
) {

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()

    val interactDrawer = {
        scope.launch {
            drawerState.apply {
                if(isClosed) open() else close()
            }
        }
    }

    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    var isTopBarShow by remember { mutableStateOf(true) }

    val navigateToRoute = { route: String ->
        navController.navigate(route) {
            launchSingleTop = true
            restoreState = true
            popUpTo(navController.graph.startDestinationId) {
                saveState = true
            }
        }
        scope.launch { drawerState.close() }
    }

    LaunchedEffect(currentRoute) {
        isTopBarShow = currentRoute !in listOf(
            MainRoutes.PostDetails.route,
            MainRoutes.SourceDetails.route,
        )
    }

    ModalNavigationDrawer(
        modifier = Modifier.then(modifier),
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet {
                ModalDrawerSheet(
                    modifier = Modifier.requiredWidth(320.dp)
                ) {
                    MainDrawerContent(
                        modifier = Modifier.fillMaxWidth(),
                        currentRoute = currentRoute
                    ) { event ->
                        when(event) {
                            MainDrawerContentEvent.NavigateHomeScreen -> {
                                navigateToRoute(MainRoutes.Home.route)
                            }
                            MainDrawerContentEvent.NavigateExploreScreen -> {
                                navigateToRoute(MainRoutes.Explore.route)
                            }
                            MainDrawerContentEvent.NavigateFeedsScreen -> {
                                navigateToRoute(MainRoutes.FeedSources.route)
                            }
                            MainDrawerContentEvent.NavigateSettingsScreen -> {
                                navigateToRoute(MainRoutes.Settings.route)
                            }
                            MainDrawerContentEvent.SignOutUser -> {
                                onLogout()
                            }
                        }
                    }
                }
            }
        },
    ) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = {
                AnimatedVisibility(
                    visible = isTopBarShow
                ) {
                    TopAppBar(
                        modifier = Modifier.fillMaxWidth(),
                        onMenuSelect = { interactDrawer() },
                        onProfileSelect = {
                            onProfileNavigation()
                        }
                    )
                }
            }
        ) { innerPadding ->
            MainNavigationGraph(
                modifier = Modifier
                    .fillMaxSize()
                    .let {
                        if(isTopBarShow) {
                            it.padding(innerPadding)
                        } else {
                            it.padding(top = 0.dp)
                        }
                    },
                navController = navController
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
            onProfileNavigation = {},
            onLogout = {},
        )
    }
}
