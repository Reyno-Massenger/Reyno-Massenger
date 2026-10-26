import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

/// Comprehensive 2026/2027 design system inspired by Telegram and modern iOS/Material 3.
/// Built with deep color psychology:
/// - Sapphire Azure (#2481CC): Evokes digital trust, calm focus, speed, and privacy.
/// - Emerald Mint (#10B981): Immediate positive feedback, active presence, security.
/// - Midnight Slate (#0E1621 / #17212B): Deep contrast, zero eye strain, AMOLED efficiency.
/// - Layered Porcelain (#F4F6FB / #FFFFFF): Airy, breathable, ultra-clean surfaces.
class AppTheme {
  // Brand Primary & Accent Colors
  static const Color primaryColor = Color(0xFF2481CC);
  static const Color primaryColorDark = Color(0xFF1A65A4);
  static const Color secondaryColor = Color(0xFF00ACC1);
  static const Color accentColor = Color(0xFF10B981);
  static const Color warningColor = Color(0xFFF59E0B);
  static const Color dangerColor = Color(0xFFEF4444);
  static const Color purpleColor = Color(0xFF8B5CF6);
  static const Color cyanAccent = Color(0xFF4FC3F7);

  // Dark Theme Colors (Telegram Night Palette)
  static const Color darkCanvas = Color(0xFF0E1621);
  static const Color darkSurface = Color(0xFF17212B);
  static const Color darkCard = Color(0xFF1E2C3A);
  static const Color darkBubblePeer = Color(0xFF242F3D);
  static const Color darkBubbleSelf = Color(0xFF2B5278);
  static const Color darkBorder = Color(0xFF27384A);

  // Light Theme Colors (Telegram Day Palette)
  static const Color lightCanvas = Color(0xFFF4F6FB);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightCard = Color(0xFFFFFFFF);
  static const Color lightBubblePeer = Color(0xFFFFFFFF);
  static const Color lightBubbleSelf = Color(0xFF2481CC);
  static const Color lightBorder = Color(0xFFE2E8F0);

  // Gradient definitions
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF2AABEE), Color(0xFF229ED9), Color(0xFF2481CC)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient storyGradient = LinearGradient(
    colors: [Color(0xFFF58529), Color(0xFFDD2A7B), Color(0xFF8134AF), Color(0xFF515BD4)],
    begin: Alignment.bottomLeft,
    end: Alignment.topRight,
  );

  static const LinearGradient bubbleSelfGradientLight = LinearGradient(
    colors: [Color(0xFF2BAAEB), Color(0xFF2292D5)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient bubbleSelfGradientDark = LinearGradient(
    colors: [Color(0xFF2E5B88), Color(0xFF264C72)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static ThemeData get lightTheme {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.light,
      primary: primaryColor,
      onPrimary: Colors.white,
      primaryContainer: const Color(0xFFE3F2FD),
      onPrimaryContainer: const Color(0xFF0D47A1),
      secondary: secondaryColor,
      onSecondary: Colors.white,
      surface: lightSurface,
      onSurface: const Color(0xFF1E293B),
      error: dangerColor,
      onError: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: colorScheme,
      fontFamily: 'Vazirmatn',
      scaffoldBackgroundColor: lightCanvas,
      canvasColor: lightCanvas,
      cardColor: lightCard,
      dividerColor: lightBorder,
      splashFactory: InkSparkle.splashFactory,
      appBarTheme: const AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 1.5,
        centerTitle: false,
        backgroundColor: Colors.white,
        foregroundColor: Color(0xFF0F172A),
        surfaceTintColor: Colors.transparent,
        shadowColor: Color(0x0F000000),
        titleTextStyle: TextStyle(
          fontFamily: 'Vazirmatn',
          fontSize: 19,
          fontWeight: FontWeight.w700,
          color: Color(0xFF0F172A),
          letterSpacing: -0.2,
        ),
        iconTheme: IconThemeData(color: Color(0xFF1E293B)),
        actionsIconTheme: IconThemeData(color: Color(0xFF1E293B)),
      ),
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: ZoomPageTransitionsBuilder(),
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.windows: ZoomPageTransitionsBuilder(),
          TargetPlatform.linux: ZoomPageTransitionsBuilder(),
          TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
        },
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: lightCard,
        shadowColor: Colors.black.withValues(alpha: 0.04),
        shape: RoundedRectangleBorder(
          borderRadius: const BorderRadius.all(Radius.circular(16)),
          side: BorderSide(color: lightBorder.withValues(alpha: 0.8), width: 0.8),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Vazirmatn',
            fontWeight: FontWeight.w600,
            fontSize: 15,
            letterSpacing: -0.1,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primaryColor,
          side: const BorderSide(color: Color(0xFFBFDBFE), width: 1.2),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 13),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Vazirmatn',
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primaryColor,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Vazirmatn',
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: lightSurface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        hintStyle: TextStyle(
          color: Colors.blueGrey.shade300,
          fontSize: 14,
          fontWeight: FontWeight.w400,
        ),
        labelStyle: TextStyle(
          color: Colors.blueGrey.shade600,
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: lightBorder, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: lightBorder, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: primaryColor, width: 1.8),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: dangerColor, width: 1.2),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: dangerColor, width: 1.8),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 3,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: lightSurface,
        selectedItemColor: primaryColor,
        unselectedItemColor: Color(0xFF94A3B8),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: lightSurface,
        elevation: 0,
        height: 64,
        indicatorColor: primaryColor.withValues(alpha: 0.12),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: primaryColor, size: 24);
          }
          return const IconThemeData(color: Color(0xFF64748B), size: 22);
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: primaryColor,
              fontFamily: 'Vazirmatn',
            );
          }
          return const TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w500,
            color: Color(0xFF64748B),
            fontFamily: 'Vazirmatn',
          );
        }),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: lightSurface,
        selectedColor: primaryColor.withValues(alpha: 0.14),
        side: BorderSide(color: lightBorder, width: 0.8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        labelStyle: const TextStyle(
          fontFamily: 'Vazirmatn',
          fontSize: 13,
          fontWeight: FontWeight.w500,
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: lightSurface,
        elevation: 6,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
        ),
        titleTextStyle: const TextStyle(
          fontFamily: 'Vazirmatn',
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: Color(0xFF0F172A),
        ),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: lightSurface,
        elevation: 12,
        modalBackgroundColor: lightSurface,
        modalElevation: 12,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
        ),
        showDragHandle: true,
        dragHandleColor: Color(0xFFCBD5E1),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        displayMedium: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        displaySmall: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        headlineLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Color(0xFF0F172A)),
        headlineMedium: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Color(0xFF0F172A)),
        headlineSmall: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Color(0xFF0F172A)),
        titleLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Color(0xFF0F172A)),
        titleMedium: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w600, color: Color(0xFF0F172A)),
        titleSmall: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w600, color: Color(0xFF334155)),
        bodyLarge: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF1E293B)),
        bodyMedium: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF475569)),
        bodySmall: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF64748B)),
        labelLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w600, color: Color(0xFF1E293B)),
        labelMedium: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF64748B)),
        labelSmall: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF94A3B8)),
      ),
    );
  }

  static ThemeData get darkTheme {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.dark,
      primary: const Color(0xFF42A5F5),
      onPrimary: Colors.white,
      primaryContainer: const Color(0xFF1E3A5F),
      onPrimaryContainer: const Color(0xFFBFDBFE),
      secondary: secondaryColor,
      onSecondary: Colors.white,
      surface: darkSurface,
      onSurface: const Color(0xFFF1F5F9),
      error: dangerColor,
      onError: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: colorScheme,
      fontFamily: 'Vazirmatn',
      scaffoldBackgroundColor: darkCanvas,
      canvasColor: darkCanvas,
      cardColor: darkCard,
      dividerColor: darkBorder,
      splashFactory: InkSparkle.splashFactory,
      appBarTheme: const AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: false,
        backgroundColor: darkSurface,
        foregroundColor: Colors.white,
        titleTextStyle: TextStyle(
          fontFamily: 'Vazirmatn',
          fontSize: 19,
          fontWeight: FontWeight.w700,
          color: Colors.white,
          letterSpacing: -0.2,
        ),
        iconTheme: IconThemeData(color: Colors.white),
        actionsIconTheme: IconThemeData(color: Colors.white),
      ),
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: ZoomPageTransitionsBuilder(),
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.windows: ZoomPageTransitionsBuilder(),
          TargetPlatform.linux: ZoomPageTransitionsBuilder(),
          TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
        },
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: darkCard,
        shadowColor: Colors.black.withValues(alpha: 0.3),
        shape: RoundedRectangleBorder(
          borderRadius: const BorderRadius.all(Radius.circular(16)),
          side: BorderSide(color: darkBorder.withValues(alpha: 0.7), width: 0.8),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF42A5F5),
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Vazirmatn',
            fontWeight: FontWeight.w600,
            fontSize: 15,
            letterSpacing: -0.1,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF64B5F6),
          side: const BorderSide(color: Color(0xFF1E3A8A), width: 1.2),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 13),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Vazirmatn',
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF64B5F6),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Vazirmatn',
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkSurface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        hintStyle: const TextStyle(
          color: Color(0xFF64748B),
          fontSize: 14,
          fontWeight: FontWeight.w400,
        ),
        labelStyle: const TextStyle(
          color: Color(0xFF94A3B8),
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: darkBorder, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: darkBorder, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFF42A5F5), width: 1.8),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: dangerColor, width: 1.2),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: dangerColor, width: 1.8),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: const Color(0xFF42A5F5),
        foregroundColor: Colors.white,
        elevation: 3,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: darkSurface,
        selectedItemColor: Color(0xFF42A5F5),
        unselectedItemColor: Color(0xFF64748B),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: darkSurface,
        elevation: 0,
        height: 64,
        indicatorColor: const Color(0xFF42A5F5).withValues(alpha: 0.16),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: Color(0xFF42A5F5), size: 24);
          }
          return const IconThemeData(color: Color(0xFF94A3B8), size: 22);
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: Color(0xFF42A5F5),
              fontFamily: 'Vazirmatn',
            );
          }
          return const TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w500,
            color: Color(0xFF94A3B8),
            fontFamily: 'Vazirmatn',
          );
        }),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: darkSurface,
        selectedColor: const Color(0xFF42A5F5).withValues(alpha: 0.2),
        side: BorderSide(color: darkBorder, width: 0.8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        labelStyle: const TextStyle(
          fontFamily: 'Vazirmatn',
          fontSize: 13,
          fontWeight: FontWeight.w500,
          color: Colors.white,
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: darkSurface,
        elevation: 8,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
        ),
        titleTextStyle: const TextStyle(
          fontFamily: 'Vazirmatn',
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: darkSurface,
        elevation: 12,
        modalBackgroundColor: darkSurface,
        modalElevation: 12,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
        ),
        showDragHandle: true,
        dragHandleColor: Color(0xFF475569),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.bold, color: Colors.white),
        displayMedium: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.bold, color: Colors.white),
        displaySmall: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.bold, color: Colors.white),
        headlineLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Colors.white),
        headlineMedium: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Colors.white),
        headlineSmall: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Colors.white),
        titleLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w700, color: Colors.white),
        titleMedium: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w600, color: Colors.white),
        titleSmall: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w600, color: Color(0xFFE2E8F0)),
        bodyLarge: TextStyle(fontFamily: 'Vazirmatn', color: Colors.white),
        bodyMedium: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFFCBD5E1)),
        bodySmall: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF94A3B8)),
        labelLarge: TextStyle(fontFamily: 'Vazirmatn', fontWeight: FontWeight.w600, color: Colors.white),
        labelMedium: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF94A3B8)),
        labelSmall: TextStyle(fontFamily: 'Vazirmatn', color: Color(0xFF64748B)),
      ),
    );
  }
}
