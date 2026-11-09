package com.pawfect.app.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChatBubble
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Person
import androidx.compose.ui.graphics.vector.ImageVector

/**
 * Navigation routes covering the complete 8-screen application flow.
 * [FROM MARKDOWN: Section 2 & Phase 5]
 */
sealed class NavRoute(val route: String) {
    // Screen 1: Splash / Welcome
    object Welcome : NavRoute("welcome")

    // Screen 2: Interactive Onboarding
    object Onboarding : NavRoute("onboarding")

    // Screen 3: AI Matchmaker Chat
    object Chat : NavRoute("chat")

    // Screen 4: Your Perfect Match!
    object Matches : NavRoute("matches")

    // Screen 5: Pet Detail Screen
    object PetDetail : NavRoute("pet_detail/{petId}") {
        fun createRoute(petId: String) = "pet_detail/$petId"
    }

    // Screen 6: Compatibility Analysis
    object Compatibility : NavRoute("compatibility/{petId}") {
        fun createRoute(petId: String) = "compatibility/$petId"
    }

    // Screen 7: Adoption Process Stepper
    object AdoptionStepper : NavRoute("adoption_stepper/{petId}") {
        fun createRoute(petId: String) = "adoption_stepper/$petId"
    }

    // Screen 8: User Profile Hub
    object Profile : NavRoute("profile")
}

/**
 * 3 Primary persistent bottom navigation destinations.
 * [FROM MARKDOWN: Step 4.2] "persistent NavigationBar supporting 3 primary destinations: Home, Matches, and Profile."
 */
sealed class BottomNavItem(
    val route: String,
    val title: String,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector
) {
    object Home : BottomNavItem(
        route = NavRoute.Welcome.route,
        title = "Home",
        selectedIcon = Icons.Filled.Home,
        unselectedIcon = Icons.Outlined.Home
    )

    object Matches : BottomNavItem(
        route = NavRoute.Matches.route,
        title = "Matches",
        selectedIcon = Icons.Filled.Favorite,
        unselectedIcon = Icons.Outlined.FavoriteBorder
    )

    object Chat : BottomNavItem(
        route = NavRoute.Chat.route,
        title = "AI Chat",
        selectedIcon = Icons.Filled.ChatBubble,
        unselectedIcon = Icons.Outlined.ChatBubbleOutline
    )

    object Profile : BottomNavItem(
        route = NavRoute.Profile.route,
        title = "Profile",
        selectedIcon = Icons.Filled.Person,
        unselectedIcon = Icons.Outlined.Person
    )
}

