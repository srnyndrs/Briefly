package com.srnyndrs.android.briefly.ui.screen.content.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ExitToApp
import androidx.compose.material.icons.outlined.Settings
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun DrawerContent(
    modifier: Modifier = Modifier,
    currentRoute: String?,
    onNavigation: (route: String) -> Unit
) {

    val scrollState = rememberScrollState()
    val menuOptions = listOf(
        "Home" to "content_explore",
        "Explore" to "article_search",
        "Feed Search" to "feed_search",
    )

    Column(
        modifier = Modifier.then(modifier)
            .padding(horizontal = 16.dp)
            .verticalScroll(scrollState)
    ) {
        Spacer(Modifier.height(12.dp))
        Text(
            modifier = Modifier.padding(16.dp),
            text = "Briefly",
            style = MaterialTheme.typography.titleLarge,
        )
        HorizontalDivider()
        Text(
            modifier = Modifier.padding(16.dp),
            text ="Section 1",
            style = MaterialTheme.typography.titleMedium
        )
        repeat(menuOptions.size) { index ->
            val (title, route) = menuOptions[index]
            NavigationDrawerItem(
                label = {
                    Text(
                        text = title
                    )
                },
                selected = currentRoute == route,
                icon = { Icon(Icons.Outlined.Settings, contentDescription = null) },
                //badge = { Text("20") }, // Placeholder
                onClick = {
                    onNavigation(route)
                }
            )
        }
        HorizontalDivider()
        Text(
            modifier = Modifier.padding(16.dp),
            text ="Section 2",
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
                    imageVector = Icons.AutoMirrored.Outlined.ExitToApp,
                    contentDescription = null // TODO
                )
            },
            onClick = {
                // TODO: Logout
            }
        )
    }
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
                    ) { }
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