# React Native and Expo libraries

Prefer packages from the Expo SDK and check that a library supports the New Architecture and the project's Expo SDK version before adding it; a library with native code needs a development build, not Expo Go. Names are npm packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Navigation | `expo-router` | `@react-navigation/native` | Expo Router is file-based and built on React Navigation |
| Animation | `react-native-reanimated` | | |
| Gestures | `react-native-gesture-handler` | | |
| Custom drawing and shaders | `@shopify/react-native-skia` | | |
| Long lists | `@shopify/flash-list` | `FlatList` | |
| Key-value storage | `react-native-mmkv` | `expo-secure-store` | Secrets and tokens go in secure storage |
| Local database | `expo-sqlite` | `@nozbe/watermelondb` | WatermelonDB for offline-first sync |
| Styling | `nativewind` | `react-native-unistyles`, `tamagui` | NativeWind brings Tailwind classes; Tamagui is a full component kit |
| Images | `expo-image` | | |
| Server state | `@tanstack/react-query` | | |
| Client state | `zustand` | | |
| Forms | `react-hook-form` with `zod` | | |
| Component tests | `@testing-library/react-native` | | |
| End-to-end tests | Maestro | | A command-line tool, not an npm package |
| In-app purchases | `react-native-purchases` | | RevenueCat: a paid service with a free tier |
| Crash reporting | `@sentry/react-native` | | |
