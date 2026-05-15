package com.srnyndrs.android.briefly.domain.usecase.auth

import javax.inject.Inject

class AllAuthUseCase @Inject constructor(
    val loginUseCase: LoginUseCase,
    val registerUseCase: RegisterUseCase,
    val refreshSessionUseCase: RefreshSessionUseCase,
)
