package com.pawfect.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.pawfect.app.ui.screens.adoption.AdoptionStepperScreen
import com.pawfect.app.ui.screens.chat.ChatScreen
import com.pawfect.app.ui.screens.compatibility.CompatibilityScreen
import com.pawfect.app.ui.screens.matches.MatchesScreen
import com.pawfect.app.ui.screens.onboarding.OnboardingScreen
import com.pawfect.app.ui.screens.petdetail.PetDetailScreen
import com.pawfect.app.ui.screens.profile.ProfileScreen
import com.pawfect.app.ui.screens.welcome.WelcomeScreen

/**
 * Complete 8-screen navigation graph for PawFect.
 * [FROM MARKDOWN: Section 2, Step 4.2, and Phase 5]
 */
@Composable
fun PawFectNavGraph(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = NavRoute.Welcome.route,
        modifier = modifier
    ) {
        // Screen 1: Splash / Welcome
        composable(NavRoute.Welcome.route) {
            WelcomeScreen(
                onGetStarted = { navController.navigate(NavRoute.Onboarding.route) },
                onSkipToChat = { navController.navigate(NavRoute.Chat.route) }
            )
        }

        // Screen 2: Interactive Onboarding
        composable(NavRoute.Onboarding.route) {
            OnboardingScreen(
                onFinishOnboarding = {
                    navController.navigate(NavRoute.Chat.route) {
                        popUpTo(NavRoute.Welcome.route) { inclusive = false }
                    }
                }
            )
        }

        // Screen 3: AI Matchmaker Chat
        composable(NavRoute.Chat.route) {
            ChatScreen(
                onViewPetDetail = { petId ->
                    navController.navigate(NavRoute.PetDetail.createRoute(petId))
                },
                onViewCompatibility = { petId ->
                    navController.navigate(NavRoute.Compatibility.createRoute(petId))
                }
            )
        }

        // Screen 4: Your Perfect Match!
        composable(NavRoute.Matches.route) {
            MatchesScreen(
                onSelectPet = { petId ->
                    navController.navigate(NavRoute.PetDetail.createRoute(petId))
                },
                onStartChat = {
                    navController.navigate(NavRoute.Chat.route)
                }
            )
        }

        // Screen 5: Pet Detail Screen
        composable(
            route = NavRoute.PetDetail.route,
            arguments = listOf(navArgument("petId") { type = NavType.StringType })
        ) { backStackEntry ->
            val petId = backStackEntry.arguments?.getString("petId") ?: ""
            PetDetailScreen(
                petId = petId,
                onBack = { navController.popBackStack() },
                onStartAdoptionChat = {
                    navController.navigate(NavRoute.Chat.route)
                },
                onViewCompatibility = {
                    navController.navigate(NavRoute.Compatibility.createRoute(petId))
                },
                onApply = {
                    navController.navigate(NavRoute.AdoptionStepper.createRoute(petId))
                }
            )
        }

        // Screen 6: Compatibility Analysis
        composable(
            route = NavRoute.Compatibility.route,
            arguments = listOf(navArgument("petId") { type = NavType.StringType })
        ) { backStackEntry ->
            val petId = backStackEntry.arguments?.getString("petId") ?: ""
            CompatibilityScreen(
                petId = petId,
                onBack = { navController.popBackStack() },
                onContinueToAdoption = {
                    navController.navigate(NavRoute.AdoptionStepper.createRoute(petId))
                }
            )
        }

        // Screen 7: Adoption Process Stepper
        composable(
            route = NavRoute.AdoptionStepper.route,
            arguments = listOf(navArgument("petId") { type = NavType.StringType })
        ) { backStackEntry ->
            val petId = backStackEntry.arguments?.getString("petId") ?: ""
            AdoptionStepperScreen(
                petId = petId,
                onBack = { navController.popBackStack() },
                onComplete = {
                    navController.navigate(NavRoute.Matches.route) {
                        popUpTo(NavRoute.Welcome.route) { inclusive = false }
                    }
                }
            )
        }

        // Screen 8: User Profile Hub
        composable(NavRoute.Profile.route) {
            ProfileScreen(
                onNavigateToMatches = { navController.navigate(NavRoute.Matches.route) },
                onNavigateToSavedPets = { navController.navigate(NavRoute.Matches.route) },
                onNavigateToChatHistory = { navController.navigate(NavRoute.Chat.route) }
            )
        }
    }
}

