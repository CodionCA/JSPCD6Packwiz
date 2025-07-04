#ifndef INCLUDE_SKY
    #define INCLUDE_SKY

    #define SUN_GLARE_AMOUNT 10 // [0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30]
    #define MOON_GLARE_AMOUNT 10 // [0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30]

    #include "/lib/colors/lightAndAmbientColors.glsl"
    #include "/lib/colors/skyColors.glsl"

    #ifdef CAVE_FOG
        #include "/lib/atmospherics/fog/caveFactor.glsl"
    #endif

    vec3 GetSky(float VdotU, float VdotS, float dither, bool doGlare, bool doGround) {
        // Prepare variables
        float nightFactorSqrt2 = sqrt2(nightFactor);
        float nightFactorM = sqrt2(nightFactorSqrt2) * 0.4;
        float VdotSM1 = pow2(max(VdotS, 0.0));
        float VdotSM2 = pow2(VdotSM1);
        float VdotSM3 = pow2(pow2(max(-VdotS, 0.0)));
        float VdotSML = sunVisibility > 0.5 ? VdotS : -VdotS;

        float VdotUmax0 = max(VdotU, 0.0);
        float VdotUmax0M = 1.0 - pow2(VdotUmax0);

        // Prepare colors
        vec3 upColor = mix(nightUpSkyColor * (1.5 - 0.5 * nightFactorSqrt2 + nightFactorM * VdotSM3 * 1.5), dayUpSkyColor, sunFactor);
        vec3 middleColor = mix(nightMiddleSkyColor * (3.0 - 2.0 * nightFactorSqrt2), dayMiddleSkyColor * (1.0 + VdotSM2 * 0.3), sunFactor);
        vec3 downColor = mix(nightDownSkyColor, dayDownSkyColor, (sunFactor + sunVisibility) * 0.5);

        // Mix the colors
            // Set sky gradient
            float scatteredGroundMixerMult = 1.0;
            float spookyMiddleMult = 1.0;
            #ifdef SPOOKY
                scatteredGroundMixerMult = 0.2;
                spookyMiddleMult = 0.8;
            #endif
            float VdotUM1 = pow2(1.0 - VdotUmax0);
                  VdotUM1 = pow(VdotUM1, 1.0 - VdotSM2 * 0.4);
                  VdotUM1 = mix(VdotUM1, 1.0, rainFactor2 * 0.15);
            vec3 finalSky = mix(upColor, middleColor * spookyMiddleMult, VdotUM1);

            // Add sunset color
            float VdotUM2 = pow2(1.0 - abs(VdotU));
                  VdotUM2 = VdotUM2 * VdotUM2 * (3.0 - 2.0 * VdotUM2);
                  VdotUM2 *= (0.7 - nightFactorM + VdotSM1 * (0.3 + nightFactorM)) * invNoonFactor * sunFactor;
            finalSky = mix(finalSky, sunsetDownSkyColorP * (1.0 + VdotSM1 * 0.3), VdotUM2 * invRainFactor);

            // Add sky ground with fake light scattering
            float VdotUM3 = min(max0(-VdotU + 0.08) / 0.35, 1.0);
                  VdotUM3 = smoothstep1(VdotUM3);
            vec3 scatteredGroundMixer = vec3(VdotUM3 * VdotUM3, sqrt1(VdotUM3), sqrt3(VdotUM3));
                 scatteredGroundMixer = mix(vec3(VdotUM3), scatteredGroundMixer, 0.75 - 0.5 * rainFactor);
            finalSky = mix(finalSky, downColor, scatteredGroundMixer * scatteredGroundMixerMult);
        //

        // Sky Ground
        if (doGround)
            finalSky *= smoothstep1(pow2(1.0 + min(VdotU, 0.0)));

        // Apply Underwater Fog
        if (isEyeInWater == 1)
            finalSky = mix(finalSky * 3.0, waterFogColor, VdotUmax0M);

    // Sun/Moon Glare
        #if SUN_GLARE_AMOUNT > 0 || MOON_GLARE_AMOUNT > 0
        if (doGlare) {
            if (0.0 < VdotSML) {
                float glareScatter = 4.0 * (2.0 - clamp01(VdotS * 1000.0));
                float VdotSM4 = pow(abs(VdotS), glareScatter);

                float visfactor = 0.075;
                float glare = visfactor / (1.0 - (1.0 - visfactor) * VdotSM4) - visfactor;

                glare *= 0.5 + pow2(noonFactor) * 1.2;
                glare *= 1.0 - rainFactor * 0.5;

                float glareWaterFactor = isEyeInWater * sunVisibility;
                vec3 moonGlareColor = vec3(0.38, 0.4, 0.5);
                #if defined SPOOKY && BLOOD_MOON > 0
                    moonGlareColor = mix(moonGlareColor, vec3(1.0, 0.0, 0.0) * 1.5, getBloodMoon(moonPhase, sunVisibility));
                #endif
                vec3 glareColor = mix(moonGlareColor * 0.7, vec3(0.5), sunVisibility);
                    glareColor = glareColor + glareWaterFactor * vec3(7.0);

                glare *= mix(MOON_GLARE_AMOUNT * 0.1, SUN_GLARE_AMOUNT * 0.1, sunVisibility);

                #ifdef SPOOKY
                    glare *= 0.5;
                #endif

                finalSky += glare * shadowTime * glareColor;
            }
        }
        #endif

        #ifdef CAVE_FOG
            // Apply Cave Fog
            finalSky = mix(finalSky, caveFogColor, GetCaveFactor() * VdotUmax0M);
        #endif

        // Dither to fix banding
        finalSky += (dither - 0.5) / 128.0;

        #if RETRO_LOOK == 1
            finalSky = vec3(0.0);
        #elif RETRO_LOOK ==2
            finalSky = mix(finalSky, vec3(0.0), nightVision);
        #endif

        return finalSky;
    }

    vec3 GetLowQualitySky(float VdotU, float VdotS, float dither, bool doGlare, bool doGround) {
        // Prepare variables
        float VdotUmax0 = max(VdotU, 0.0);
        float VdotUmax0M = 1.0 - pow2(VdotUmax0);

        // Prepare colors
        vec3 upColor = mix(nightUpSkyColor, dayUpSkyColor, sunFactor);
        vec3 middleColor = mix(nightMiddleSkyColor, dayMiddleSkyColor, sunFactor);

        // Mix the colors
            // Set sky gradient
            float VdotUM1 = pow2(1.0 - VdotUmax0);
                  VdotUM1 = mix(VdotUM1, 1.0, rainFactor2 * 0.2);
            vec3 finalSky = mix(upColor, middleColor, VdotUM1);

            // Add sunset color
            float VdotUM2 = pow2(1.0 - abs(VdotU));
                  VdotUM2 *= invNoonFactor * sunFactor * (0.8 + 0.2 * VdotS);
            finalSky = mix(finalSky, sunsetDownSkyColorP * (shadowTime * 0.6 + 0.2), VdotUM2 * invRainFactor);
        //

        // Sky Ground
        finalSky *= pow2(pow2(1.0 + min(VdotU, 0.0)));

        // Apply Underwater Fog
        if (isEyeInWater == 1)
            finalSky = mix(finalSky, waterFogColor, VdotUmax0M);

        // Sun/Moon Glare
        finalSky *= 1.0 + mix(nightFactor, 0.5 + 0.7 * noonFactor, VdotS * 0.5 + 0.5) * pow2(pow2(pow2(VdotS)));

        #ifdef CAVE_FOG
            // Apply Cave Fog
            finalSky = mix(finalSky, caveFogColor, GetCaveFactor() * VdotUmax0M);
        #endif

        #if RETRO_LOOK == 1 || RETRO_LOOK == 2
            finalSky = vec3(0.0);
        #endif

        return finalSky;
    }

#endif //INCLUDE_SKY