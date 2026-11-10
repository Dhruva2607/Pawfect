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
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
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
    var energy by remember { mutableFloatStateOf(3f) }
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(uiState.session) {
        if (uiState.session != null) onAuthenticated()
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
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
            }
            Spacer(Modifier.height(8.dp))
            Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                PawLogo(Modifier.padding(14.dp).size(34.dp))
            }
            Spacer(Modifier.height(20.dp))
            Text(
                if (isSignUp) "Let's find your match" else "Welcome back",
                style = MaterialTheme.typography.displaySmall
            )
            Spacer(Modifier.height(6.dp))
            Text(
                if (isSignUp) "Create an account and tell us a little about home."
                else "Sign in to pick up where you left off.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(24.dp))

            AuthModeToggle(isSignUp) {
                isSignUp = it
                viewModel.clearError()
            }

            Spacer(Modifier.height(20.dp))
            if (isSignUp) {
                AuthField(name, { name = it }, "Full name", Icons.Outlined.Person)
                Spacer(Modifier.height(12.dp))
            }
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

            if (isSignUp) {
                Spacer(Modifier.height(20.dp))
                HomePreferencesCard(
                    housingType = housingType,
                    onHousingType = { housingType = it },
                    hasChildren = hasChildren,
                    onHasChildren = { hasChildren = it },
                    hasOtherPets = hasOtherPets,
                    onHasOtherPets = { hasOtherPets = it },
                    energy = energy,
                    onEnergy = { energy = it }
                )
            }

            Spacer(Modifier.height(24.dp))
            Button(
                onClick = {
                    viewModel.authenticate(
                        isSignUp = isSignUp,
                        name = name,
                        email = email,
                        password = password,
                        housingType = housingType,
                        hasChildren = hasChildren,
                        hasOtherPets = hasOtherPets,
                        energyBudget = energy.toInt()
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
                    Text(if (isSignUp) "Create account" else "Log in")
                }
            }
            TextButton(
                onClick = {
                    isSignUp = !isSignUp
                    viewModel.clearError()
                },
                modifier = Modifier.align(Alignment.CenterHorizontally)
            ) {
                Text(if (isSignUp) "Already have an account? Log in" else "New to PawFect? Sign up")
            }
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
private fun AuthModeToggle(isSignUp: Boolean, onChange: (Boolean) -> Unit) {
    Surface(shape = CircleShape, color = MaterialTheme.colorScheme.surfaceVariant) {
        Row(Modifier.fillMaxWidth().padding(4.dp)) {
            listOf("Sign up" to true, "Log in" to false).forEach { (label, value) ->
                val selected = isSignUp == value
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(CircleShape)
                        .background(
                            if (selected) MaterialTheme.colorScheme.primary else Color.Transparent
                        )
                        .clickable { onChange(value) }
                        .padding(vertical = 10.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        label,
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = if (selected) {
                            MaterialTheme.colorScheme.onPrimary
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                }
            }
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
private fun HomePreferencesCard(
    housingType: String,
    onHousingType: (String) -> Unit,
    hasChildren: Boolean,
    onHasChildren: (Boolean) -> Unit,
    hasOtherPets: Boolean,
    onHasOtherPets: (Boolean) -> Unit,
    energy: Float,
    onEnergy: (Float) -> Unit
) {
    Surface(
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
    ) {
        Column(Modifier.fillMaxWidth().padding(16.dp)) {
            Text("A little about your home", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                listOf("Apartment" to "apartment", "House with yard" to "house_with_yard").forEach { (label, value) ->
                    FilterChip(
                        selected = housingType == value,
                        onClick = { onHousingType(value) },
                        label = { Text(label) },
                        shape = CircleShape
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            PreferenceSwitch("Children at home", hasChildren, onHasChildren)
            PreferenceSwitch("Other pets at home", hasOtherPets, onHasOtherPets)
            Spacer(Modifier.height(4.dp))
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Activity level", style = MaterialTheme.typography.bodyMedium)
                Text(
                    "${energy.toInt()}/5",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            Slider(value = energy, onValueChange = onEnergy, valueRange = 1f..5f, steps = 3)
        }
    }
}

@Composable
private fun PreferenceSwitch(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}
