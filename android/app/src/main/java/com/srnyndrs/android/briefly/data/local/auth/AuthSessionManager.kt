package com.srnyndrs.android.briefly.data.local.auth

import android.content.SharedPreferences
import androidx.core.content.edit
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

@Singleton
class AuthSessionManager @Inject constructor(
    private val sharedPreferences: SharedPreferences,
) {

    companion object {
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
    }

    private val _authState = MutableStateFlow<AuthState>(AuthState.Loading)
    val authState = _authState.asStateFlow()

    fun getAccessToken(): String? = sharedPreferences.getString(
        KEY_ACCESS_TOKEN,
        null,
    )

    fun getRefreshToken(): String? = sharedPreferences.getString(
        KEY_REFRESH_TOKEN,
        null,
    )

    fun saveTokens(accessToken: String, refreshToken: String) {
        sharedPreferences.edit {
            putString(KEY_ACCESS_TOKEN, accessToken)
            putString(KEY_REFRESH_TOKEN, refreshToken)
        }
        _authState.value = AuthState.Authenticated
    }

    fun invalidateTokens() {
        sharedPreferences.edit {
            remove(KEY_ACCESS_TOKEN)
            remove(KEY_REFRESH_TOKEN)
        }
        _authState.value = AuthState.Unauthenticated
    }

    fun setLoading() {
        _authState.value = AuthState.Loading
    }

    fun markUnavailable() {
        _authState.value = AuthState.Unavailable
    }

}
