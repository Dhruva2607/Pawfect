package com.pawfect.app.di

import com.pawfect.app.BuildConfig
import com.pawfect.app.data.local.SessionManager
import com.pawfect.app.data.remote.PawFectApiService
import com.pawfect.app.data.remote.PawFectSseClient
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Named
import javax.inject.Singleton

/**
 * Hilt Dependency Injection module for Networking and Remote Clients.
 * [FROM MARKDOWN: Section 4 & Step 4.1]
 */
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    /**
     * Android Emulator loopback routing to local FastAPI host.
     * [FROM MARKDOWN: Section 4] "Routes local traffic from Android Emulator via http://10.0.2.2:8000/api/v1/"
     */
    @Provides
    @Singleton
    @Named("BaseUrl")
    fun provideBaseUrl(): String = BuildConfig.API_BASE_URL.let {
        if (it.endsWith("/")) it else "$it/"
    }

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
        coerceInputValues = true
    }

    private fun buildClient(sessionManager: SessionManager, readTimeoutSeconds: Long): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BASIC
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
        return OkHttpClient.Builder()
            .addInterceptor(logging)
            .addInterceptor { chain ->
                val token = sessionManager.currentSession()?.token
                val request = chain.request().newBuilder().apply {
                    if (!token.isNullOrBlank()) {
                        header("Authorization", "Bearer $token")
                    }
                }.build()
                chain.proceed(request)
            }
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(readTimeoutSeconds, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(sessionManager: SessionManager): OkHttpClient =
        buildClient(sessionManager, readTimeoutSeconds = 60)

    /**
     * Long-lived client for Server-Sent Events. A 0 read timeout disables it so
     * slow model turns are not aborted while waiting for the first token.
     */
    @Provides
    @Singleton
    @Named("SseClient")
    fun provideSseOkHttpClient(sessionManager: SessionManager): OkHttpClient =
        buildClient(sessionManager, readTimeoutSeconds = 0)

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        json: Json,
        @Named("BaseUrl") baseUrl: String
    ): Retrofit {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
    }

    @Provides
    @Singleton
    fun providePawFectApiService(retrofit: Retrofit): PawFectApiService {
        return retrofit.create(PawFectApiService::class.java)
    }
}
