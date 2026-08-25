package com.srnyndrs.android.briefly.ui.screen.profile.screen

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.screen.profile.components.UserCard
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ProfileScreen(
    modifier: Modifier = Modifier
) {
    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        UserCard(
            onEdit = {

            },
            onDelete = {

            }
        )
        HorizontalDivider(
            modifier = Modifier.padding(horizontal = 6.dp),
            thickness = 1.dp,
            color = MaterialTheme.colorScheme.onSurface
        )
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 6.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Top,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(
                    modifier = Modifier.weight(0.6f),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "Language Preferences",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = "The language of the content",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.W300
                    )
                }
                Column(
                    modifier = Modifier.weight(0.3f)
                ) {
                    DropdownMenu(
                        expanded = false,
                        onDismissRequest = {  },
                    ) {
                        DropdownMenuItem(
                            text = {
                                Text(
                                    text = "English"
                                )
                            },
                            onClick = {

                            }
                        )
                    }
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun ProfileScreenPreview() {
    BrieflyTheme {
        Surface {
            ProfileScreen(
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}
