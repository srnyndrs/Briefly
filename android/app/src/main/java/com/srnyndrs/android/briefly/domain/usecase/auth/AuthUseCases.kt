package com.srnyndrs.android.briefly.domain.usecase.auth

import javax.inject.Inject

class AuthUseCases @Inject constructor(
    val loginUseCase: LoginUseCase,
    val registerUseCase: RegisterUseCase,
)
