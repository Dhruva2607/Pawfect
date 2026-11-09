package com.pawfect.app.ui.screens.welcome

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/**
 * Screen 1: Splash / Welcome
 * [FROM MARKDOWN: Phase 5 - Screen 1]
 * Illustration, branding badge, and prominent "Get Started" button leading to onboarding.
 */
@Composable
fun WelcomeScreen(
    onGetStarted: () -> Unit,
    onSkipToChat: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Badge(containerColor = MaterialTheme.colorScheme.primaryContainer) {
            Text(
                text = "🐾 AI PET MATCHMAKER",
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                style = MaterialTheme.typography.labelSmall
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = "Find Your\nPerfect Pet Companion",
            style = MaterialTheme.typography.headlineLarge,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = "Goodbye rigid filters. Say hello to intelligent, lifestyle-aligned adoption counseling.",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(48.dp))

        Button(
            onClick = onGetStarted,
            modifier = Modifier
                .fillMaxWidth()
                .height(54.dp),
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
        ) {
            Text("Get Started")
        }

        Spacer(modifier = Modifier.height(12.dp))

        TextButton(onClick = onSkipToChat) {
            Text("Skip directly to AI Chat")
        }
    }
}

