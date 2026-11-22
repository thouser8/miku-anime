/*
 * Copyright (C) 2024-2025 OpenAni and contributors.
 *
 * 此源代码的使用受 GNU AFFERO GENERAL PUBLIC LICENSE version 3 许可证的约束, 可以在以下链接找到该许可证.
 * Use of this source code is governed by the GNU AGPLv3 license, which can be found at the following link.
 *
 * https://github.com/open-ani/ani/blob/main/LICENSE
 */

package me.him188.ani.app.ui.foundation

import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import me.him188.ani.app.foundation.R

/**
 * 内置全局字体: 苹方 (PingFang SC), 文件由 CI 在构建期下载注入 res/font
 * (见 .github/workflows/miku-build.yml), 不随源码分发.
 */
private val bundledFontFamily: FontFamily = FontFamily(
    Font(R.font.app_font, FontWeight.Normal),
    Font(R.font.app_font_semibold, FontWeight.SemiBold),
)

@Composable
actual fun rememberPlatformFontFamily(fontName: String?): PlatformFontFamily {
    return PlatformFontFamily(bundledFontFamily)
}
