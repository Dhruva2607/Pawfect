package com.pawfect.app.ui.screens.adoption

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.ui.components.AdoptionStep
import com.pawfect.app.ui.components.AdoptionStepperBar
import com.pawfect.app.ui.components.PawLogo
import com.pawfect.app.ui.components.PawTag
import com.pawfect.app.ui.viewmodel.AdoptionViewModel

/**
 * Screen 7: Adoption Process Stepper
 * [FROM MARKDOWN: Phase 5 - Screen 7]
 * Visual horizontal stepper (Match -> Review -> Apply), celebration graphic,
 * and "Fill Adoption Form" / "Save for Later" actions.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdoptionStepperScreen(
    petId: String,
    onBack: () -> Unit,
    onComplete: () -> Unit,
    viewModel: AdoptionViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(petId) {
        viewModel.loadPet(petId)
    }

    var applicantName by remember { mutableStateOf(uiState.applicantName) }
    var applicantEmail by remember { mutableStateOf(uiState.applicantEmail) }
    var applicantPhone by remember { mutableStateOf(uiState.applicantPhone) }
    var housingDetails by remember { mutableStateOf(uiState.housingDetails) }
    var householdMembers by remember { mutableStateOf(uiState.householdMembers) }
    var notes by remember { mutableStateOf(uiState.notes) }

    LaunchedEffect(
        uiState.applicantName,
        uiState.applicantEmail,
        uiState.applicantPhone,
        uiState.housingDetails,
        uiState.householdMembers,
        uiState.notes
    ) {
        applicantName = uiState.applicantName
        applicantEmail = uiState.applicantEmail
        applicantPhone = uiState.applicantPhone
        housingDetails = uiState.housingDetails
        householdMembers = uiState.householdMembers
        notes = uiState.notes
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                            PawLogo(Modifier.padding(7.dp).size(18.dp))
                        }
                        Spacer(Modifier.width(10.dp))
                        Text("Adoption journey", style = MaterialTheme.typography.headlineSmall)
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Visual horizontal stepper (Match -> Review -> Apply)
            AdoptionStepperBar(currentStep = uiState.currentStep)

            Spacer(modifier = Modifier.height(20.dp))

            if (uiState.error != null) {
                Surface(
                    color = MaterialTheme.colorScheme.errorContainer,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
                ) {
                    Text(
                        uiState.error.orEmpty(),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }

            if (uiState.isSubmitted) {
                // Celebration Graphic & Confirmation [FROM MARKDOWN: Screen 7]
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = MaterialTheme.shapes.extraLarge,
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(28.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Box(
                            modifier = Modifier
                                .size(72.dp)
                                .background(MaterialTheme.colorScheme.primaryContainer, CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Default.Check,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(34.dp)
                            )
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(
                            text = "Application Submitted!",
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        Text(
                            text = "Your application for ${uiState.pet?.name ?: "your match"} has been received. You can check its current status here.",
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        Spacer(modifier = Modifier.height(20.dp))

                        uiState.applicationResult?.applicationId?.let { applicationId ->
                            Text(
                                "Application ID",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(Modifier.height(4.dp))
                            PawTag(applicationId)
                        }

                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            "Current stage: ${uiState.applicationResult?.stageStatus?.replaceFirstChar { it.uppercase() } ?: "Submitted"}",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        TextButton(
                            onClick = viewModel::refreshApplicationStatus,
                            enabled = !uiState.isRefreshingStatus
                        ) {
                            if (uiState.isRefreshingStatus) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(18.dp),
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Text("Refresh application status")
                            }
                        }
                        Spacer(modifier = Modifier.height(16.dp))

                        Button(
                            onClick = onComplete,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(50.dp),
                            shape = MaterialTheme.shapes.medium
                        ) {
                            Text("Back to matches")
                        }
                    }
                }
            } else {
                // Adoption Application Form [FROM MARKDOWN: Screen 7]
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = MaterialTheme.shapes.extraLarge,
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text(
                            text = "Adoption application",
                            style = MaterialTheme.typography.headlineSmall
                        )
                        Text(
                            text = "Applying to adopt ${uiState.pet?.name ?: "your matched companion"}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        OutlinedTextField(
                            value = applicantName,
                            onValueChange = { applicantName = it },
                            label = { Text("Full Name") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = MaterialTheme.shapes.small
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        OutlinedTextField(
                            value = applicantEmail,
                            onValueChange = { applicantEmail = it },
                            label = { Text("Email Address") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = MaterialTheme.shapes.small
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        OutlinedTextField(
                            value = applicantPhone,
                            onValueChange = { applicantPhone = it },
                            label = { Text("Phone Number") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = MaterialTheme.shapes.small
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        OutlinedTextField(
                            value = housingDetails,
                            onValueChange = { housingDetails = it },
                            label = { Text("Home & Balcony/Yard Description") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = MaterialTheme.shapes.small
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        OutlinedTextField(
                            value = householdMembers,
                            onValueChange = { householdMembers = it },
                            label = { Text("Household members & other pets") },
                            modifier = Modifier.fillMaxWidth(),
                            maxLines = 2,
                            shape = MaterialTheme.shapes.small
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        OutlinedTextField(
                            value = notes,
                            onValueChange = { notes = it },
                            label = { Text("Message to Shelter Staff") },
                            modifier = Modifier.fillMaxWidth(),
                            maxLines = 3,
                            shape = MaterialTheme.shapes.small
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        // Actions: "Fill Adoption Form" (Submit) / "Save for Later" [FROM MARKDOWN: Screen 7]
                        Button(
                            onClick = {
                                viewModel.submitApplication(
                                    petId = petId,
                                    applicantName = applicantName,
                                    applicantEmail = applicantEmail,
                                    applicantPhone = applicantPhone,
                                    housingDetails = housingDetails,
                                    householdMembers = householdMembers,
                                    notes = notes
                                )
                            },
                            enabled = !uiState.isLoading && uiState.pet != null,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp),
                            shape = MaterialTheme.shapes.medium,
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                        ) {
                            if (uiState.isLoading) {
                                CircularProgressIndicator(
                                    color = MaterialTheme.colorScheme.onPrimary,
                                    modifier = Modifier.size(24.dp)
                                )
                            } else {
                                Text("Submit application")
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        OutlinedButton(
                            onClick = onBack,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(48.dp),
                            shape = MaterialTheme.shapes.medium
                        ) {
                            Text("Back")
                        }
                    }
                }
            }
        }
    }
}
