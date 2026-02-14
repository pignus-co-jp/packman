
| 種類 | 命名 | override | super 必須 | 役割 |
|------|------|----------|------------|-------|
| **Public Method** | `snake_case` | 任意 | 場合により必須 | 外部 API / 処理の流れ |
| **Protected Method** | `_snake_case` | 任意 | 任意 | 内部処理（継承可） |
| **Private Method** | `__snake_case` | 不可 | 不要 | 完全内部処理 |
| **Implementation Hook** | `_CamelCase` | **必須** | 不要 | テンプレート内部の実装フック |
| **Event Hook** | `_on_...` | 任意 | 不要 | 拡張ポイント（イベント） |

