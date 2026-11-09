package com.pawfect.app.di

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
    fun provideBaseUrl(): String = "http://10.0.2.2:8000/api/v1/"

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
        coerceInputValues = true
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        return OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }

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

