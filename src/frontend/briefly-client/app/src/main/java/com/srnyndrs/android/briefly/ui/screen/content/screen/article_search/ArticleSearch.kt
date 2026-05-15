package com.srnyndrs.android.briefly.ui.screen.content.screen.article_search

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.common.SearchTextField
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ArticleSearch(
    modifier: Modifier = Modifier
) {

    var query by rememberSaveable {
        mutableStateOf("")
    }

    Column(
        modifier = Modifier.then(modifier)
            .padding(6.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Screen Title
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = "Article Search",
            style = MaterialTheme.typography.headlineSmall,
            textAlign = TextAlign.Center
        )
        // Search bar
        SearchTextField(
            modifier = Modifier.fillMaxWidth(),
            value = query,
            onValueChange = {
                query = it
            },
            placeholder = "Search Articles"
        ) {
            // TODO: invoke search
        }
        // Article list
    }
}

@PreviewLightDark
@Composable
fun ArticleSearchPreview() {
    BrieflyTheme {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = {
                TopAppBar(
                    onMenuSelect = {}
                ) { }
            }
        ) { paddingValues ->
            ArticleSearch(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
            )
        }
    }
}