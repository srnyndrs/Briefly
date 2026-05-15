package com.srnyndrs.android.briefly.ui.screen.auth.screen.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.srnyndrs.android.briefly.ui.screen.auth.components.AuthFormContainer
import com.srnyndrs.android.briefly.ui.screen.auth.components.EmailTextField
import com.srnyndrs.android.briefly.ui.screen.auth.components.PasswordTextField
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun LoginScreen(
    modifier: Modifier = Modifier,
    onNavigation: () -> Unit,
    onLogin: (String, String) -> Unit
) {

    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }

    val validation = {
        email.isNotEmpty() && password.isNotEmpty()
    }

    Column(
        modifier = Modifier.then(modifier),
        verticalArrangement = Arrangement.spacedBy(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.Center,
            ) {
                Text(
                    text = "Welcome Back!",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Medium
                )
            }
            AuthFormContainer(
                modifier = Modifier.fillMaxWidth(),
                items = {
                    listOf(
                        {
                            EmailTextField(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = 48.dp),
                                value = email,
                                onValueChange = {
                                    email = it
                                },
                                label = "Email"
                            )
                        },
                        {
                            PasswordTextField(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = 48.dp),
                                value = password,
                                onValueChange = {
                                    password = it
                                },
                                label = "Password",
                                passwordVisible = passwordVisible,
                                onPasswordVisibilityChange = { passwordVisible = it }
                            )
                        },
                        {
                            Button(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = 48.dp),
                                shape = RoundedCornerShape(5.dp),
                                onClick = {
                                    if(validation()) {
                                        onLogin(email, password)
                                    }
                                }
                            ) {
                                Text(
                                    text = "Login",
                                )
                            }
                        }
                    )
                }
            )
        }
        TextButton(
            onClick = {
                onNavigation()
            }
        ) {
            Text(
                text = "Don't have an account yet? Create one here"
            )
        }
    }
}

@PreviewLightDark
@Composable
fun LoginScreenPreview() {
    BrieflyTheme {
        Surface {
            LoginScreen(
                modifier = Modifier.fillMaxSize(),
                onNavigation = {}
            ) { _,_ -> }
        }
    }
}