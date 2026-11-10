package com.pawfect.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

/**
 * Root Scaffold with persistent NavigationBar.
 * [FROM MARKDOWN: Step 4.2]
 * "Implement a root Scaffold with a persistent NavigationBar supporting 3 primary destinations:
 * Home (Onboarding/Dashboard), Matches, and Profile."
 */
@Composable
fun PawFectMainScaffold(
    isAuthenticated: Boolean,
    onLogout: () -> Unit
) {
    val navController = rememberNavController()
    var authenticated by remember { mutableStateOf(isAuthenticated) }
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val bottomNavItems = listOf(
        BottomNavItem.Home,
        BottomNavItem.Chat,
        BottomNavItem.Matches,
        BottomNavItem.Profile
    )

    // Show bottom bar on primary tabs
    val showBottomBar = authenticated && currentRoute in listOf(
        NavRoute.Home.route,
        NavRoute.Chat.route,
        NavRoute.Matches.route,
        NavRoute.SavedPets.route,
        NavRoute.Profile.route
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface,
                    contentColor = MaterialTheme.colorScheme.onSurface
                ) {
                    bottomNavItems.forEach { item ->
                        val selected = currentRoute == item.route ||
                            (item == BottomNavItem.Matches && currentRoute == NavRoute.SavedPets.route)
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                if (currentRoute != item.route) {
                                    navController.navigate(item.route) {
                                        popUpTo(NavRoute.Home.route) {
                                            saveState = true
                                        }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            },
                            icon = {
                                Icon(
                                    imageVector = if (selected) item.selectedIcon else item.unselectedIcon,
                                    contentDescription = item.title
                                )
                            },
                            label = { Text(text = item.title) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        PawFectNavGraph(
            navController = navController,
            modifier = Modifier.padding(innerPadding),
            startDestination = if (isAuthenticated) NavRoute.Home.route else NavRoute.Welcome.route,
            onAuthenticated = { authenticated = true },
            onLogout = {
                onLogout()
                authenticated = false
                navController.navigate(NavRoute.Welcome.route) {
                    popUpTo(navController.graph.startDestinationId) { inclusive = true }
                    launchSingleTop = true
                }
            }
        )
    }
}
