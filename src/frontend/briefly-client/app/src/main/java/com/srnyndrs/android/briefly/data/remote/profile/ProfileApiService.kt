package com.srnyndrs.android.briefly.data.remote.profile

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.patch
import io.ktor.client.request.setBody

class ProfileApiService (
    private val client: HttpClient
) {

    companion object {
        private const val BASE_PROFILE_PATH = "me"
        private const val PREFERENCES_PATH = "me"
    }

    suspend fun getProfile(): ProfileDataResponseDto {
        return client.get(BASE_PROFILE_PATH)
            .body()
    }

    suspend fun getPreferences(): PreferencesDto {
        return client.get("$BASE_PROFILE_PATH/$PREFERENCES_PATH")
            .body()
    }

    suspend fun updatePreferences(request: PreferenceUpdateRequestDto): PreferencesDto {
        return client.patch("$BASE_PROFILE_PATH/$PREFERENCES_PATH") {
            setBody(request)
        }.body()
    }

}
