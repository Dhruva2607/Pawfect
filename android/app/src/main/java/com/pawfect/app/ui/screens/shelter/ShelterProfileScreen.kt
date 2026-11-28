package com.pawfect.app.ui.screens.shelter

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.model.ShelterUpdateRequestDto
import com.pawfect.app.ui.viewmodel.ShelterProfileViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShelterProfileScreen(
    onLogout: () -> Unit,
    viewModel: ShelterProfileViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var name by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var address by remember { mutableStateOf("") }
    var city by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }
    var hours by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }

    LaunchedEffect(uiState.shelter) {
        uiState.shelter?.let { s ->
            name = s.name
            phone = s.contactPhone
            address = s.address
            city = s.city
            state = s.state
            hours = s.operatingHours.orEmpty()
            description = s.description.orEmpty()
        }
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Center Profile", fontWeight = FontWeight.Bold) }) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Center Name") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = phone, onValueChange = { phone = it }, label = { Text("Phone") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = address, onValueChange = { address = it }, label = { Text("Address") }, modifier = Modifier.fillMaxWidth())
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = city, onValueChange = { city = it }, label = { Text("City") }, modifier = Modifier.weight(1f))
                OutlinedTextField(value = state, onValueChange = { state = it }, label = { Text("State") }, modifier = Modifier.weight(1f))
            }
            OutlinedTextField(value = hours, onValueChange = { hours = it }, label = { Text("Operating Hours") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = description, onValueChange = { description = it }, label = { Text("Description") }, modifier = Modifier.fillMaxWidth(), minLines = 3)

            if (uiState.savedBanner) {
                Text("Profile saved ✓", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Medium)
            }
            if (!uiState.error.isNullOrBlank()) {
                Text(uiState.error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }

            Button(
                onClick = {
                    viewModel.save(
                        ShelterUpdateRequestDto(
                            name = name.trim(),
                            contactPhone = phone.trim(),
                            address = address.trim(),
                            city = city.trim(),
                            state = state.trim(),
                            operatingHours = hours.takeIf { it.isNotBlank() },
                            description = description.takeIf { it.isNotBlank() }
                        )
                    )
                },
                enabled = !uiState.isSaving,
                modifier = Modifier.fillMaxWidth().height(50.dp)
            ) {
                Text("Save Profile")
            }

            OutlinedButton(
                onClick = onLogout,
                modifier = Modifier.fillMaxWidth().height(48.dp)
            ) {
                Text("Log Out")
            }
        }
    }
}
