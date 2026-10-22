package com.srnyndrs.android.briefly.ui.screen.auth.screen.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthFormState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthScreenState

object AuthPreviewData {
    val form = AuthFormState(
        email = "reader@example.com",
        password = "example-password",
    )
}

class AuthFormStateProvider : PreviewParameterProvider<AuthFormState> {
    override val values = sequenceOf(
        AuthFormState(),
        AuthPreviewData.form,
        AuthFormState(validationRequested = true),
    )
}

class AuthScreenStateProvider : PreviewParameterProvider<AuthScreenState> {
    override val values = sequenceOf(
        AuthScreenState(),
        AuthScreenState(login = AuthPreviewData.form),
        AuthScreenState(
            isRegistering = true,
            registration = AuthPreviewData.form,
        ),
        AuthScreenState(
            login = AuthPreviewData.form,
            submission = UiState.Loading,
        ),
        AuthScreenState(
            login = AuthPreviewData.form,
            submission = UiState.Error(message = ""),
        ),
        AuthScreenState(login = AuthFormState(validationRequested = true)),
    )
}
