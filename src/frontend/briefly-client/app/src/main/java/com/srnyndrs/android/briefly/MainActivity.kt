package com.srnyndrs.android.briefly

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.srnyndrs.android.briefly.ui.navigation.AppNavigation
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            BrieflyTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    AppNavigation(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding),
                        navController = rememberNavController()
                    )
                }
            }
        }
    }
}
