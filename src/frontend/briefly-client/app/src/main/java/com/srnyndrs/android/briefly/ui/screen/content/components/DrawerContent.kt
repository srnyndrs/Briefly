package com.srnyndrs.android.briefly.ui.screen.content.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.solid.ArrowRightOnRectangle
import com.composables.icons.heroicons.solid.Home
import com.composables.icons.heroicons.solid.Newspaper
import com.composables.icons.heroicons.solid.Rss
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun DrawerContent(
    modifier: Modifier = Modifier,
    currentRoute: String?,
    onDrawerEvent: (DrawerContentEvent) -> Unit
) {

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier.then(modifier)
            .padding(horizontal = 16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Spacer(Modifier.height(12.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                modifier = Modifier.size(32.dp),
                imageVector = Heroicons.Solid.Newspaper,
                contentDescription = null // TODO
            )
            Text(
                modifier = Modifier.padding(16.dp),
                text = "Briefly",
                style = MaterialTheme.typography.titleLarge,
            )
        }
        HorizontalDivider()
        Text(
            modifier = Modifier.padding(16.dp),
            text ="General",
            style = MaterialTheme.typography.titleMedium
        )
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            NavigationDrawerItem(
                label = {
                    Text(
                        text = "Home"
                    )
                },
                selected = currentRoute == "content_explore",
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.Home,
                        contentDescription = null
                    )
                },
                onClick = {
                    onDrawerEvent(DrawerContentEvent.NavigateHomeScreen)
                }
            )
            NavigationDrawerItem(
                label = {
                    Text(
                        text = "Feeds"
                    )
                },
                selected = currentRoute == "feed_search",
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.Rss,
                        contentDescription = null
                    )
                },
                onClick = {
                    onDrawerEvent(DrawerContentEvent.NavigateFeedsScreen)
                }
            )
        }
        HorizontalDivider()
        Text(
            modifier = Modifier.padding(16.dp),
            text ="Account",
            style = MaterialTheme.typography.titleMedium
        )
        NavigationDrawerItem(
            label = {
                Text(
                    text = "Sign Out"
                )
            },
            selected = false,
            icon = {
                Icon(
                    imageVector = Heroicons.Solid.ArrowRightOnRectangle,
                    contentDescription = null // TODO
                )
            },
            onClick = {
                onDrawerEvent(DrawerContentEvent.SignOutUser)
            }
        )
    }
}

sealed class DrawerContentEvent {
    data object NavigateHomeScreen: DrawerContentEvent()
    data object NavigateFeedsScreen: DrawerContentEvent()
    data object SignOutUser: DrawerContentEvent()
}

@PreviewLightDark
@Composable
fun DrawerContentPreview() {
    BrieflyTheme {
        ModalNavigationDrawer(
            drawerState = rememberDrawerState(initialValue = DrawerValue.Open),
            drawerContent = {
                ModalDrawerSheet(
                    modifier = Modifier.requiredWidth(320.dp)
                ) {
                    DrawerContent(
                        modifier = Modifier.fillMaxWidth(),
                        currentRoute = "content_explore"
                    ) { _ -> }
                }
            }
        ) {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = {
                    TopAppBar(
                        modifier = Modifier.fillMaxWidth(),
                        onMenuSelect = {}
                    ) { }
                }
            ) { paddingValues ->
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                ) {

                }
            }
        }
    }
}