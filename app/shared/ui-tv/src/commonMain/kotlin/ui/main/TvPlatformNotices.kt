/*
 * Copyright (C) 2024-2026 OpenAni and contributors.
 *
 * 此源代码的使用受 GNU AFFERO GENERAL PUBLIC LICENSE version 3 许可证的约束, 可以在以下链接找到该许可证.
 * Use of this source code is governed by the GNU AGPLv3 license, which can be found at the following link.
 *
 * https://github.com/open-ani/ani/blob/main/LICENSE
 */

package me.him188.ani.app.ui.main

import androidx.compose.runtime.Composable

/**
 * 有没看过的应用内通知 (侧边栏头像带红点, 点头像落在账号页「通知」那一行). 通知只有安卓有 (见 TvNotices),
 * 别的端恒为 false.
 */
@Composable
internal expect fun rememberTvPlatformNoticesFresh(): Boolean
