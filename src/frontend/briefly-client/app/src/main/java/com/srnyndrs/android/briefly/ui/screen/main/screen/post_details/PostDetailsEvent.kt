package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

sealed class PostDetailsEvent {
    data object RetryLoad : PostDetailsEvent()
    data class MuteKeyword(val keyword: String): PostDetailsEvent()
}
