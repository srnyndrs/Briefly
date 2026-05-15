package com.srnyndrs.android.briefly.ui.screen.auth.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun AuthFormContainer(
    modifier: Modifier = Modifier,
    items: () -> List<@Composable () -> Unit>
) {
    Column(
        modifier = Modifier.then(modifier)
            .fillMaxWidth()
            .padding(vertical = 6.dp, horizontal = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        items().forEach { composable ->
            composable()
        }
    }
}

@PreviewLightDark
@Composable
private fun AuthFormContainerPreview() {
    BrieflyTheme {
        Surface {
            AuthFormContainer(
                items = {
                    listOf(
                        {
                            EmailTextField(
                                modifier = Modifier.fillMaxWidth(),
                                value = "sample@email.com",
                                onValueChange = {},
                                label = "Email"
                            )
                        },
                        {
                            PasswordTextField(
                                modifier = Modifier.fillMaxWidth(),
                                value = "password",
                                onValueChange = {},
                                label = "Password",
                                passwordVisible = false,
                                onPasswordVisibilityChange = {}
                            )
                        }
                    )
                }
            )
        }
    }
}
