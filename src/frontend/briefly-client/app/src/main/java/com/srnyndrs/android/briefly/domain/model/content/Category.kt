package com.srnyndrs.android.briefly.domain.model.content

import com.srnyndrs.android.briefly.R

enum class Category(val stringResId: Int) {
    POLITICS(R.string.category_type_politics),
    WORLD(R.string.category_type_world),
    BUSINESS(R.string.category_type_business),
    ECONOMY(R.string.category_type_economy),
    FINANCE(R.string.category_type_finance),
    TECHNOLOGY(R.string.category_type_technology),
    SCIENCE(R.string.category_type_science),
    HEALTH(R.string.category_type_health),
    ENVIRONMENT(R.string.category_type_environment),
    SPORTS(R.string.category_type_sports),
    ENTERTAINMENT(R.string.category_type_entertainment),
    LIFESTYLE(R.string.category_type_lifestyle),
    SOCIETY(R.string.category_type_society),
    AUTOMOTIVE(R.string.category_type_automotive),
    OTHER(R.string.category_type_other)
}
