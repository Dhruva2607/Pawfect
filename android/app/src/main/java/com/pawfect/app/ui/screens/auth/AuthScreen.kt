package com.pawfect.app.ui.screens.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.Email
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.model.GeneratedProfileResponseDto
import com.pawfect.app.ui.components.PawLogo
import com.pawfect.app.ui.viewmodel.AuthViewModel

@Composable
fun AuthScreen(
    initialSignUp: Boolean,
    onBack: () -> Unit,
    onAuthenticated: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    var isSignUp by remember(initialSignUp) { mutableStateOf(initialSignUp) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var housingType by remember { mutableStateOf("apartment") }
    var hasChildren by remember { mutableStateOf(false) }
    var hasOtherPets by remember { mutableStateOf(false) }
    var energy by remember { mutableStateOf(3) }
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(uiState.session) {
        if (uiState.session != null && (!isSignUp || uiState.signUpStep == 5)) {
            onAuthenticated()
        }
    }
    LaunchedEffect(uiState.error) {
        uiState.error?.let { snackbarHostState.showSnackbar(it) }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = MaterialTheme.colorScheme.background
    ) { insets ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(insets)
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 12.dp)
        ) {
            IconButton(
                onClick = {
                    if (isSignUp && uiState.signUpStep in 1..4) {
                        viewModel.previousSignUpStep()
                    } else {
                        onBack()
                    }
                }
            ) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
            }
            Spacer(Modifier.height(8.dp))
            Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                PawLogo(Modifier.padding(14.dp).size(34.dp))
            }
            Spacer(Modifier.height(20.dp))
            Text(
                when {
                    !isSignUp -> "Welcome back"
                    uiState.signUpStep == 0 -> "Let's find your match"
                    uiState.signUpStep == 5 -> "Your profile is ready"
                    else -> "A little about your home"
                },
                style = MaterialTheme.typography.displaySmall
            )
            Spacer(Modifier.height(6.dp))
            Text(
                when {
                    !isSignUp -> "Sign in to pick up where you left off."
                    uiState.signUpStep == 0 -> "Create an account to begin your profile."
                    uiState.signUpStep == 5 -> "We saved your preferences to personalize your matches."
                    else -> "Question ${uiState.signUpStep} of 4 · Tap an answer to continue."
                },
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            if (isSignUp) {
                Spacer(Modifier.height(16.dp))
                LinearProgressIndicator(
                    progress = { (uiState.signUpStep.coerceIn(0, 5) + 1) / 6f },
                    modifier = Modifier.fillMaxWidth().clip(CircleShape),
                    color = MaterialTheme.colorScheme.primary,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant
                )
            }

            Spacer(Modifier.height(24.dp))

            if (!isSignUp) {
                AuthField(
                    value = email,
                    onValueChange = { email = it },
                    label = "Email address",
                    icon = Icons.Outlined.Email,
                    keyboardType = KeyboardType.Email
                )
                Spacer(Modifier.height(12.dp))
                AuthField(
                    value = password,
                    onValueChange = { password = it },
                    label = "Password",
                    icon = Icons.Outlined.Lock,
                    keyboardType = KeyboardType.Password,
                    isPassword = true
                )
                Spacer(Modifier.height(24.dp))
                Button(
                    onClick = { viewModel.login(email = email, password = password) },
                    enabled = !uiState.isLoading,
                    modifier = Modifier.fillMaxWidth().height(54.dp),
                    shape = MaterialTheme.shapes.medium
                ) {
                    if (uiState.isLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                    } else {
                        Text("Log in")
                    }
                }
                TextButton(
                    onClick = {
                        isSignUp = true
                        viewModel.resetSignUpFlow()
                    },
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                ) {
                    Text("New to PawFect? Sign up")
                }
            } else {
                when (uiState.signUpStep) {
                    0 -> {
                        AuthField(name, { name = it }, "Full name", Icons.Outlined.Person)
                        Spacer(Modifier.height(12.dp))
                        AuthField(
                            value = email,
                            onValueChange = { email = it },
                            label = "Email address",
                            icon = Icons.Outlined.Email,
                            keyboardType = KeyboardType.Email
                        )
                        Spacer(Modifier.height(12.dp))
                        AuthField(
                            value = password,
                            onValueChange = { password = it },
                            label = "Password",
                            icon = Icons.Outlined.Lock,
                            keyboardType = KeyboardType.Password,
                            isPassword = true
                        )
                        Spacer(Modifier.height(24.dp))
                        Button(
                            onClick = {
                                viewModel.startSignUpAccount(
                                    name = name,
                                    email = email,
                                    password = password
                                )
                            },
                            enabled = !uiState.isLoading,
                            modifier = Modifier.fillMaxWidth().height(54.dp),
                            shape = MaterialTheme.shapes.medium
                        ) {
                            if (uiState.isLoading) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.onPrimary
                                )
                            } else {
                                Text("Continue")
                            }
                        }
                    }
                    1 -> {
                        QuestionStepCard(
                            question = "What kind of living space do you have?",
                            options = listOf(
                                "Apartment" to "apartment",
                                "House with yard" to "house_with_yard"
                            ),
                            selectedValue = housingType,
                            isLoading = uiState.isLoading,
                            onSelect = { selected ->
                                housingType = selected
                                viewModel.submitHousingAnswer(selected)
                            }
                        )
                    }
                    2 -> {
                        QuestionStepCard(
                            question = "Are there children at home?",
                            options = listOf(
                                "Yes, children at home" to true,
                                "No children at home" to false
                            ),
                            selectedValue = hasChildren,
                            isLoading = uiState.isLoading,
                            onSelect = { selected ->
                                hasChildren = selected
                                viewModel.submitChildrenAnswer(selected)
                            }
                        )
                    }
                    3 -> {
                        QuestionStepCard(
                            question = "Do you have other pets at home?",
                            options = listOf(
                                "Yes, other pets at home" to true,
                                "No other pets" to false
                            ),
                            selectedValue = hasOtherPets,
                            isLoading = uiState.isLoading,
                            onSelect = { selected ->
                                hasOtherPets = selected
                                viewModel.submitOtherPetsAnswer(selected)
                            }
                        )
                    }
                    4 -> {
                        QuestionStepCard(
                            question = "What is your daily activity level?",
                            options = listOf(
                                "1/5 · Very relaxed & cozy" to 1,
                                "2/5 · Gentle daily walks" to 2,
                                "3/5 · Moderate walks & play" to 3,
                                "4/5 · Active & outdoorsy" to 4,
                                "5/5 · High-energy & athletic" to 5
                            ),
                            selectedValue = energy,
                            isLoading = uiState.isLoading,
                            onSelect = { selected ->
                                energy = selected
                                viewModel.submitEnergyAndGenerateProfile(selected)
                            }
                        )
                    }
                    else -> {
                        GeneratedProfileCard(
                            profile = uiState.generatedProfile,
                            onContinue = { viewModel.completeSignUp() }
                        )
                    }
                }

                if (uiState.signUpStep == 0) {
                    TextButton(
                        onClick = {
                            isSignUp = false
                            viewModel.clearError()
                        },
                        modifier = Modifier.align(Alignment.CenterHorizontally)
                    ) {
                        Text("Already have an account? Log in")
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
private fun AuthField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    icon: ImageVector,
    keyboardType: KeyboardType = KeyboardType.Text,
    isPassword: Boolean = false
) {
    var passwordVisible by remember { mutableStateOf(false) }
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        leadingIcon = {
            Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
        },
        trailingIcon = if (isPassword) {
            {
                IconButton(onClick = { passwordVisible = !passwordVisible }) {
                    Icon(
                        imageVector = if (passwordVisible) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility,
                        contentDescription = if (passwordVisible) "Hide password" else "Show password"
                    )
                }
            }
        } else {
            null
        },
        visualTransformation = if (isPassword && !passwordVisible) {
            PasswordVisualTransformation()
        } else {
            VisualTransformation.None
        },
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        singleLine = true,
        shape = MaterialTheme.shapes.small,
        modifier = Modifier.fillMaxWidth(),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = MaterialTheme.colorScheme.primary,
            unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant
        )
    )
}

@Composable
private fun <T> QuestionStepCard(
    question: String,
    options: List<Pair<String, T>>,
    selectedValue: T,
    isLoading: Boolean,
    onSelect: (T) -> Unit
) {
    Surface(
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                question,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(Modifier.height(2.dp))
            options.forEach { (label, value) ->
                val selected = selectedValue == value
                Surface(
                    shape = MaterialTheme.shapes.medium,
                    color = if (selected) {
                        MaterialTheme.colorScheme.primaryContainer
                    } else {
                        MaterialTheme.colorScheme.surface
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(MaterialTheme.shapes.medium)
                        .clickable(enabled = !isLoading) { onSelect(value) }
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            label,
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Normal,
                            color = if (selected) {
                                MaterialTheme.colorScheme.onPrimaryContainer
                            } else {
                                MaterialTheme.colorScheme.onSurface
                            }
                        )
                        if (isLoading && selected) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun GeneratedProfileCard(
    profile: GeneratedProfileResponseDto?,
    onContinue: () -> Unit
) {
    Surface(
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                profile?.adopterName?.let { "$it's PawFect Profile" } ?: "Your PawFect Profile",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
            if (profile != null) {
                Text("Living space: ${profile.housingSummary}", style = MaterialTheme.typography.bodyMedium)
                Text("Household: ${profile.householdSummary}", style = MaterialTheme.typography.bodyMedium)
                Text("Activity level: ${profile.activitySummary}", style = MaterialTheme.typography.bodyMedium)
                if (profile.shelterNotes.isNotEmpty()) {
                    Spacer(Modifier.height(4.dp))
                    profile.shelterNotes.forEach { note ->
                        Text(
                            "• $note",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = onContinue,
                modifier = Modifier.fillMaxWidth().height(54.dp),
                shape = MaterialTheme.shapes.medium
            ) {
                Text("Continue to PawFect")
            }
        }
    }
}
