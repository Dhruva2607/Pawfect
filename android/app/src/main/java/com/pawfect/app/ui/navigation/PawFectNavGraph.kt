package com.pawfect.app.ui.navigation

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.pawfect.app.ui.screens.adoption.AdoptionStepperScreen
import com.pawfect.app.ui.screens.auth.AuthScreen
import com.pawfect.app.ui.screens.chat.ChatScreen
import com.pawfect.app.ui.screens.compatibility.CompatibilityScreen
import com.pawfect.app.ui.screens.matches.MatchesScreen
import com.pawfect.app.ui.screens.home.HomeScreen
import com.pawfect.app.ui.screens.onboarding.OnboardingScreen
import com.pawfect.app.ui.screens.petdetail.PetDetailScreen
import com.pawfect.app.ui.screens.profile.ProfileScreen
import com.pawfect.app.ui.screens.shelter.*
import com.pawfect.app.ui.screens.welcome.WelcomeScreen

/**
 * Complete navigation graph for PawFect (Adopter + Shelter flows).
 */
@Composable
fun PawFectNavGraph(
    navController: NavHostController,
    modifier: Modifier = Modifier,
    startDestination: String = NavRoute.Welcome.route,
    onAuthenticated: () -> Unit,
    onShelterAuthenticated: () -> Unit = {},
    onLogout: () -> Unit,
    onShelterLogout: () -> Unit = {}
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier,
        enterTransition = {
            fadeIn(tween(260)) + slideInHorizontally(
                animationSpec = tween(260, easing = FastOutSlowInEasing)
            ) { it / 14 }
        },
        exitTransition = {
            fadeOut(tween(180)) + slideOutHorizontally(
                animationSpec = tween(260, easing = FastOutSlowInEasing)
            ) { -it / 24 }
        },
        popEnterTransition = {
            fadeIn(tween(220)) + slideInHorizontally(
                animationSpec = tween(260, easing = FastOutSlowInEasing)
            ) { -it / 14 }
        },
        popExitTransition = {
            fadeOut(tween(160)) + slideOutHorizontally(
                animationSpec = tween(220, easing = FastOutSlowInEasing)
            ) { it / 24 }
        }
    ) {
        // Screen 1: Splash / Welcome
        composable(NavRoute.Welcome.route) {
            WelcomeScreen(
                onGetStarted = { navController.navigate(NavRoute.Onboarding.route) },
                onSignUp = { navController.navigate(NavRoute.Auth.createRoute(true)) },
                onLogin = { navController.navigate(NavRoute.Auth.createRoute(false)) },
                onShelterAccess = { navController.navigate(NavRoute.ShelterAuth.createRoute(false)) }
            )
        }

        // Screen 2: Interactive Onboarding
        composable(NavRoute.Onboarding.route) {
            OnboardingScreen(
                onFinishOnboarding = {
                    navController.navigate(NavRoute.Auth.createRoute(true)) {
                        popUpTo(NavRoute.Welcome.route)
                    }
                }
            )
        }

        composable(
            route = NavRoute.Auth.route,
            arguments = listOf(navArgument("mode") { type = NavType.StringType })
        ) { backStackEntry ->
            AuthScreen(
                initialSignUp = backStackEntry.arguments?.getString("mode") != "login",
                onBack = { navController.popBackStack() },
                onAuthenticated = {
                    onAuthenticated()
                    navController.navigate(NavRoute.Home.route) {
                        popUpTo(navController.graph.startDestinationId) { inclusive = true }
                        launchSingleTop = true
                    }
                    navController.navigate(NavRoute.Chat.route) {
                        launchSingleTop = true
                    }
                }
            )
        }

        // Screen 3: AI Matchmaker Chat
        composable(NavRoute.Home.route) {
            HomeScreen(
                onViewPet = { petId -> navController.navigate(NavRoute.PetDetail.createRoute(petId)) },
                onStartChat = { navController.navigate(NavRoute.Chat.route) },
                onViewMatches = { navController.navigate(NavRoute.Matches.route) }
            )
        }

        composable(NavRoute.Chat.route) {
            ChatScreen(
                onViewPetDetail = { petId ->
                    navController.navigate(NavRoute.PetDetail.createRoute(petId))
                },
                onViewCompatibility = { petId ->
                    navController.navigate(NavRoute.Compatibility.createRoute(petId))
                },
                onStartAdoption = { petId ->
                    navController.navigate(NavRoute.AdoptionStepper.createRoute(petId))
                }
            )
        }

        // Screen 4: Your Perfect Match!
        composable(NavRoute.Matches.route) {
            MatchesScreen(
                onSelectPet = { petId ->
                    navController.navigate(NavRoute.PetDetail.createRoute(petId))
                },
                onApply = { petId ->
                    navController.navigate(NavRoute.AdoptionStepper.createRoute(petId))
                },
                onStartChat = {
                    navController.navigate(NavRoute.Chat.route)
                }
            )
        }

        composable(NavRoute.SavedPets.route) {
            MatchesScreen(
                savedOnly = true,
                onSelectPet = { petId ->
                    navController.navigate(NavRoute.PetDetail.createRoute(petId))
                },
                onApply = { petId ->
                    navController.navigate(NavRoute.AdoptionStepper.createRoute(petId))
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
                onNavigateToSavedPets = { navController.navigate(NavRoute.SavedPets.route) },
                onNavigateToChatHistory = { navController.navigate(NavRoute.Chat.route) },
                onLogout = onLogout
            )
        }

        // ── Shelter (Adoption Center) Flow ────────────────────────────
        composable(
            route = NavRoute.ShelterAuth.route,
            arguments = listOf(navArgument("mode") { type = NavType.StringType })
        ) { backStackEntry ->
            ShelterAuthScreen(
                initialSignUp = backStackEntry.arguments?.getString("mode") == "signup",
                onBack = { navController.popBackStack() },
                onAuthenticated = {
                    onShelterAuthenticated()
                    navController.navigate(NavRoute.ShelterDashboard.route) {
                        popUpTo(navController.graph.startDestinationId) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(NavRoute.ShelterDashboard.route) {
            ShelterDashboardScreen(
                onAddPet = { navController.navigate(NavRoute.ShelterPetForm.createRoute(null)) },
                onOpenNotifications = { navController.navigate(NavRoute.ShelterNotifications.route) },
                onOpenApplications = { navController.navigate(NavRoute.ShelterApplications.route) },
                onOpenApplicationDetail = { appId ->
                    navController.navigate(NavRoute.ShelterApplicationDetail.createRoute(appId))
                }
            )
        }

        composable(NavRoute.ShelterPets.route) {
            ShelterPetsScreen(
                onAddPet = { navController.navigate(NavRoute.ShelterPetForm.createRoute(null)) },
                onEditPet = { petId -> navController.navigate(NavRoute.ShelterPetForm.createRoute(petId)) }
            )
        }

        composable(
            route = NavRoute.ShelterPetForm.route,
            arguments = listOf(navArgument("petId") { type = NavType.StringType; nullable = true; defaultValue = null })
        ) { backStackEntry ->
            val petId = backStackEntry.arguments?.getString("petId")
            ShelterPetFormScreen(
                petId = petId,
                onBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() }
            )
        }

        composable(NavRoute.ShelterApplications.route) {
            ShelterApplicationsScreen(
                onOpenApplication = { appId ->
                    navController.navigate(NavRoute.ShelterApplicationDetail.createRoute(appId))
                }
            )
        }

        composable(
            route = NavRoute.ShelterApplicationDetail.route,
            arguments = listOf(navArgument("appId") { type = NavType.StringType })
        ) { backStackEntry ->
            val appId = backStackEntry.arguments?.getString("appId") ?: ""
            ShelterApplicationDetailScreen(
                appId = appId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(NavRoute.ShelterNotifications.route) {
            ShelterNotificationsScreen(
                onBack = { navController.popBackStack() },
                onOpenApplication = { appId ->
                    navController.navigate(NavRoute.ShelterApplicationDetail.createRoute(appId))
                }
            )
        }

        composable(NavRoute.ShelterProfile.route) {
            ShelterProfileScreen(onLogout = onShelterLogout)
        }
    }
}
