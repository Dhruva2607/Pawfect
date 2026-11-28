package com.pawfect.app.ui.navigation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

@Composable
fun PawFectMainScaffold(
    isAuthenticated: Boolean,
    isShelterAuthenticated: Boolean = false,
    onLogout: () -> Unit,
    onShelterLogout: () -> Unit = {}
) {
    val navController = rememberNavController()
    var authenticated by remember { mutableStateOf(isAuthenticated) }
    var shelterAuthenticated by remember { mutableStateOf(isShelterAuthenticated) }
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val adopterBottomNavItems = listOf(
        BottomNavItem.Home,
        BottomNavItem.Chat,
        BottomNavItem.Matches,
        BottomNavItem.Profile
    )

    val shelterBottomNavItems = listOf(
        BottomNavItem.ShelterDashboard,
        BottomNavItem.ShelterPets,
        BottomNavItem.ShelterApplications,
        BottomNavItem.ShelterProfile
    )

    val showAdopterBottomBar = authenticated && currentRoute in listOf(
        NavRoute.Home.route,
        NavRoute.Chat.route,
        NavRoute.Matches.route,
        NavRoute.SavedPets.route,
        NavRoute.Profile.route
    )

    val showShelterBottomBar = shelterAuthenticated && currentRoute in listOf(
        NavRoute.ShelterDashboard.route,
        NavRoute.ShelterPets.route,
        NavRoute.ShelterApplications.route,
        NavRoute.ShelterProfile.route
    )

    val startDest = when {
        isShelterAuthenticated -> NavRoute.ShelterDashboard.route
        isAuthenticated -> NavRoute.Home.route
        else -> NavRoute.Welcome.route
    }

    Scaffold(
        bottomBar = {
            if (showAdopterBottomBar || showShelterBottomBar) {
                val items = if (showShelterBottomBar) shelterBottomNavItems else adopterBottomNavItems
                val rootRoute = if (showShelterBottomBar) NavRoute.ShelterDashboard.route else NavRoute.Home.route
                Column {
                    HorizontalDivider(
                        color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.7f)
                    )
                    NavigationBar(
                        containerColor = MaterialTheme.colorScheme.surface,
                        contentColor = MaterialTheme.colorScheme.onSurface,
                        tonalElevation = 0.dp
                    ) {
                        items.forEach { item ->
                            val selected = currentRoute == item.route ||
                                (item == BottomNavItem.Matches && currentRoute == NavRoute.SavedPets.route)
                            NavigationBarItem(
                                selected = selected,
                                onClick = {
                                    if (currentRoute != item.route) {
                                        navController.navigate(item.route) {
                                            popUpTo(rootRoute) { inclusive = false }
                                            launchSingleTop = true
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
                                    selectedIconColor = MaterialTheme.colorScheme.onPrimaryContainer,
                                    selectedTextColor = MaterialTheme.colorScheme.primary,
                                    indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                                    unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                    unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            )
                        }
                    }
                }
            }
        }
    ) { innerPadding ->
        PawFectNavGraph(
            navController = navController,
            modifier = Modifier.padding(innerPadding),
            startDestination = startDest,
            onAuthenticated = { authenticated = true },
            onShelterAuthenticated = { shelterAuthenticated = true },
            onLogout = {
                onLogout()
                authenticated = false
                navController.navigate(NavRoute.Welcome.route) {
                    popUpTo(navController.graph.startDestinationId) { inclusive = true }
                    launchSingleTop = true
                }
            },
            onShelterLogout = {
                onShelterLogout()
                shelterAuthenticated = false
                navController.navigate(NavRoute.Welcome.route) {
                    popUpTo(navController.graph.startDestinationId) { inclusive = true }
                    launchSingleTop = true
                }
            }
        )
    }
}
