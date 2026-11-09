package com.pawfect.app.ui.screens.onboarding

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/**
 * Screen 2: Interactive Onboarding
 * [FROM MARKDOWN: Phase 5 - Screen 2]
 * Carousel with pager indicators, friendly bot illustration, value proposition, and Next / Skip actions.
 */
@Composable
fun OnboardingScreen(
    onFinishOnboarding: () -> Unit
) {
    var currentPage by remember { mutableIntStateOf(0) }
    val pages = listOf(
        "Chat Naturally" to "Tell our AI about your home, work hours, kids, and energy budget.",
        "Precision RAG Matching" to "We query shelter databases using vector embeddings to find compatible animals.",
        "Transparent & Grounded" to "Get honest pros and caveats to ensure a forever home."
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.End
        ) {
            TextButton(onClick = onFinishOnboarding) {
                Text("Skip")
            }
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(horizontal = 16.dp)
        ) {
            Text(
                text = "🤖",
                style = MaterialTheme.typography.headlineLarge
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = pages[currentPage].first,
                style = MaterialTheme.typography.headlineMedium,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = pages[currentPage].second,
                style = MaterialTheme.typography.bodyMedium,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Page indicator dots
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                pages.indices.forEach { index ->
                    Surface(
                        modifier = Modifier.size(if (index == currentPage) 12.dp else 8.dp),
                        shape = MaterialTheme.shapes.small,
                        color = if (index == currentPage) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant
                    ) {}
                }
            }
        }

        Button(
            onClick = {
                if (currentPage < pages.size - 1) {
                    currentPage++
                } else {
                    onFinishOnboarding()
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(54.dp)
        ) {
            Text(if (currentPage < pages.size - 1) "Next" else "Start Matchmaking")
        }
    }
}
