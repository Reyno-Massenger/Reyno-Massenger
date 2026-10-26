import 'dart:math' as math;

/// Shared chat geometry: a Fibonacci spacing rhythm and golden-section
/// proportions keep bubbles, rows, and wide-screen conversation columns calm
/// and consistent without forcing desktop dimensions onto small phones.
class ChatDesign {
  ChatDesign._();

  static const double goldenRatio = 1.61803398875;
  static const double space3 = 3;
  static const double space5 = 5;
  static const double space8 = 8;
  static const double space13 = 13;
  static const double space21 = 21;
  static const double space34 = 34;

  static double messageMaxWidth(double viewportWidth) {
    if (viewportWidth <= 600) return viewportWidth * 0.82;
    return math.min(viewportWidth / goldenRatio, 720.0).toDouble();
  }
}
