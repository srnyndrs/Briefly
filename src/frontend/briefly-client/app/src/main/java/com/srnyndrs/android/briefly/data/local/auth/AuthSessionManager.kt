package com.srnyndrs.android.briefly.data.local.auth

import android.content.Context
import androidx.core.content.edit
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthSessionManager @Inject constructor(
    @ApplicationContext context: Context,
) {

    companion object {
        private const val PREFERENCES_FILE_NAME = "auth_prefs"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
    }

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val sharedPreferences = EncryptedSharedPreferences.create(
        context,
        PREFERENCES_FILE_NAME,
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

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

    fun setLoading() {
        _authState.value = AuthState.Loading
    }

    fun saveTokens(accessToken: String, refreshToken: String) {
        sharedPreferences.edit {
            putString(KEY_ACCESS_TOKEN, accessToken)
            putString(KEY_REFRESH_TOKEN, refreshToken)
        }
        _authState.value = AuthState.Authenticated
    }

    fun invalidate() {
        sharedPreferences.edit {
            remove(KEY_ACCESS_TOKEN)
            remove(KEY_REFRESH_TOKEN)
        }
        _authState.value = AuthState.Unauthenticated
    }

    fun markUnavailable() {
        _authState.value = AuthState.Unavailable
    }
}
