package com.pawfect.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pawfect.app.ui.theme.MatchGreen
import com.pawfect.app.ui.theme.StepperActive

/**
 * 4-Stage Adoption Horizontal Stepper.
 * [FROM MARKDOWN: Screen 7 & Section 2]
 * Stages: Match -> Review -> Apply -> Adopt.
 */
enum class AdoptionStep(val title: String, val index: Int) {
    MATCH("Match", 0),
    REVIEW("Review", 1),
    APPLY("Apply", 2),
    ADOPT("Adopt", 3)
}

@Composable
fun AdoptionStepperBar(
    currentStep: AdoptionStep,
    modifier: Modifier = Modifier
) {
    val steps = AdoptionStep.values()

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        steps.forEachIndexed { index, step ->
            val isCompleted = step.index < currentStep.index
            val isCurrent = step.index == currentStep.index

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.weight(1f)
            ) {
                // Step Indicator Node
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .background(
                            color = when {
                                isCompleted -> MatchGreen
                                isCurrent -> StepperActive
                                else -> MaterialTheme.colorScheme.surfaceVariant
                            },
                            shape = CircleShape
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    if (isCompleted) {
                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = "Completed",
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                    } else {
                        Text(
                            text = "${step.index + 1}",
                            color = if (isCurrent) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = step.title,
                    fontSize = 11.sp,
                    fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Normal,
                    color = if (isCurrent) StepperActive else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Connecting line between steps
            if (index < steps.size - 1) {
                Box(
                    modifier = Modifier
                        .height(2.dp)
                        .weight(0.6f)
                        .background(
                            if (index < currentStep.index) MatchGreen else MaterialTheme.colorScheme.surfaceVariant
                        )
                )
            }
        }
    }
}

