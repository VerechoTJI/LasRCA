# LasRCA：GPT-6 Luna OAuth 接入與驗證

## 結果

2026-10-04 已完成官方 OAuth 登入、ID token 簽章／issuer／audience／nonce 驗證，以及 `gpt-6-luna` 實際推論。最小連線測試回傳 `LUNA_OK`。公開 100 cases/subgraphs 結果中的 case 6（node-5）完成四階段、六次模型請求，最後的 `exact_fault_type` 輸出通過原始 `update_dataset.py` 的 JSON 擷取方式及 fault type 對照檢查。65 項測試通過。

這證明傳輸與下游格式能正常接續，並不證明兩個模型的故障判斷相同，也不是 100 cases 的標註品質評估。驗證使用臨時資料夾，結束後移除；未寫入正式標籤、修改公開案例選擇或重訓模型。

## 改動及原因

- 原本 GPT-4 Chat Completions 呼叫改由 `LunaClient.complete()` 呼叫官方公開 Responses API。OAuth 需要 `store=false` 與 `stream=true`，因此在傳輸層收集文字，僅完整成功後回傳原本階段需要的字串；中斷、失敗、空回答均停止處理，避免半份回答變成標籤。
- 第一、二、三階段、摘要階段及 explanation 的模型呼叫改為 `gpt-6-luna`。原有 prompt template、user message 內容、階段次序與檔案格式保留，沒有新增 agent/system prompt、工具或跨請求對話記憶。
- 第三階段原先寫入 iteration prompt 資料夾，卻讀取另一個相對路徑。改為讀取剛寫出的同一個檔案，讓這個既有錯誤不再阻止四階段串接。
- `common.py` 不再於 import 時索取 API key。OAuth 在第一次實際請求時讀取 LasRCA 自己的憑證；不讀取或修改 Codex 登入憑證。
- 主機識別固定使用官方接受的 `urn:uuid:<UUIDv4>`。憑證以 Windows DPAPI 加密、原子更新並排除 Git；到期前更新 access token 和 rotating refresh token，使用跨程序鎖避免更新競爭。新增 JWT 簽章驗證依賴。

資料前處理、選樣、訓練、label mapping、`update_dataset.py` 均未改動。為維持既有路徑相容，原資料集輸出檔名的 `_GPT4` 字尾仍保留；使用 Luna 後該字尾不代表實際模型。未使用的 `generate_gpt_query()` 是原先 Batch API 的 GPT-4 請求產生器，保留歷史行為；本次 OAuth 路徑不使用 Batch API。

## 操作

在 `E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/code`，使用專案 `.venv/Scripts/python.exe` 執行：

```powershell
.\.venv\Scripts\python.exe -m llm.luna_oauth login
.\.venv\Scripts\python.exe -m llm.luna_oauth check
.\.venv\Scripts\python.exe -m llm.check_pipeline
```

登入需由使用者在官方瀏覽器頁面授權。憑證位於 `code/.lasrca-oauth/account.bin`，只能由同一 Windows 帳號解密。重新授權沿用已保存的 client ID 和 host ID。測試與執行需在正常使用者環境進行，受限沙箱可能無法存取網路或 Windows DPAPI。

既有四階段可繼續從 `code/llm` 依序執行 `first_stage.py`、`second_stage.py`、`third_stage.py`、`summarization_stage.py`。這會處理既有公開 selected_samples 全部案例，不是上面的單案例驗證。尚未執行完整 100 cases，也尚未覆寫正式 response。

驗證程式會從公開 selected_samples 選擇請求數最少的非空 node/pod 案例，複製既有第一階段 prompt，直接執行同一份四階段程式，再以原始 parser 與故障類型清單檢查摘要。它不執行會寫入資料集的 update_dataset 主程式。

## 限制與恢復

目前為本機單一帳號／workspace 接入；登入不提供多帳號選單。失效或撤銷授權時需重跑 login。若程序被強制結束留下 `.lock`，確認没有 LasRCA 登入／模型請求程序使用該憑證後，刪除殘留鎖再重試。此接入只支援 Windows 憑證保護。

第一次授權曾因 host ID 格式不符被拒；改為官方 UUID URI 後成功。另一次身分驗證未通過且未啟用憑證，重試後通過；當時診斷不足，無法確定該次失敗原因，不能宣稱已找到並修正其根因。後續錯誤訊息會顯示驗證步驟與例外類型，仍不輸出憑證。

## 官方依據

- [OAuth 註冊與登入](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
- [Host ID 格式](https://developers.openai.com/siwc/token-sharing-open-source)
- [模型與 Responses 推論](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
- [Token 更新與保護](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
