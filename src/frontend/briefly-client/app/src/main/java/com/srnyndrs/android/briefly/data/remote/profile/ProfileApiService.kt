package com.srnyndrs.android.briefly.data.remote.profile

import com.srnyndrs.android.briefly.data.remote.profile.dto.PreferenceUpdateRequestDto
import com.srnyndrs.android.briefly.data.remote.profile.dto.PreferencesDto
import com.srnyndrs.android.briefly.data.remote.profile.dto.ProfileDataResponseDto
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
    }

    suspend fun getProfile(): ProfileDataResponseDto {
        return client.get(BASE_PROFILE_PATH)
            .body()
    }

    suspend fun updatePreferences(request: PreferenceUpdateRequestDto): PreferencesDto {
        return client.patch("${BASE_PROFILE_PATH}/preferences") {
            setBody(request)
        }.body()
    }

}
