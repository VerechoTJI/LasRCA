# LasRCA 工作紀錄（2026-10-04）

新進度：補上離線 `llm.export_evidence`，14／100 cases快照：653個預期entity occurrences、78個完成且合法標籤、0摘要解析失敗。保存獨立parsed labels、case層級stage3理由原文、格式錯誤、request/stage關聯、unique request token用量及成本不可得說明（不填0）。新增2項usage測試通過。runner新增失敗attempt append記錄；已執行中的runner不受修改影響，新入口重啟後才使用新增紀錄。這些是本次重現證據工具，非論文演算法。

## 權限請求失敗

使用者後續指示：先跳過全部網路與 DPAPI 操作。已停止全量 Luna runner（session 69295，Ctrl-C 結束）；完成案例為0與5，正式100案例未完成。06全量、正式07訓練與08／09完整實驗結果等待恢復網路授權；可繼續本機實作、測試、raw preprocessing 與 TS2Vec。改用 `uv run --no-sync --cache-dir ../out/uv-cache python ...`，不呼叫 Activate.ps1。

2026-10-04：為避免每次重新啟用 venv，建立正常使用者權限的持續 PowerShell（session 24409）。建立成功，但第一次後續 `write_stdin` 輸入即被工具拒絕，訊息為 `rejected by user`。Python 路徑檢查、檔案試跑、OAuth check 均未在該次工具呼叫中確認執行。停止重試此 session；此路線尚未證明可免除後續授權。原有沙箱持續 shell 的 venv／CUDA／5 tests 已驗證成功；先前單獨授權的100案例標註 session 69295 已啟動，但目前不得聲稱全量完成。

`E:/Misc/FastCodingWorkspace/AI/SMCI/reproduction_staus_original.md` 唯讀，所有進度另存本檔。沿用公開 100 cases/subgraphs，不另作選樣對照。模型為 GPT-6 Luna OAuth。

每完成一個獨立可驗收的程式任務，通過相關測試後提交一次。實驗執行結果另記，不能把 runner 完成視為實驗完成。

| 任務 | 實驗狀態 | 證據／剩餘工作 |
|---|---|---|
| OAuth 接入 | 單例驗證完成 | commit 69db66d；case6 四階段實際驗證；目前跳過網路與DPAPI |
| 0C-06 Labeling | 部分完成：2／100 cases | cases0、5 已完成；runner／resume完成；剩98cases等待恢復網路與DPAPI；正式usage與成本彙整待全量 |
| 0C-07 Dataset／重訓 | 工具完成，正式實驗未完成 | 更新與隔離輸入已驗證；等待100cases後更新獨立dataset、seeds405–409的k=1訓練 |
| 0C-08 比較 | 工具完成，正式結果未完成 | 五seed成對比較工具完成；移除std fallback後須重跑一致設定k=0與k=1；不沿用舊baseline作正式比較 |
| 0C-09 錯誤分析 | 部分完成 | 2cases／15entities已分析，1entity錯標；完整錯誤分類與案例整理等待全量；不足10個不同錯誤時如實報告 |
| 0C-10 Raw preprocessing | 抽樣部分完成，出錯停止 | topology、entity edge、time windows、raw metric轉換成功；metric generator找不到istio/adservice-0.csv。需診斷、完成Trace／Log／assembly，再擴展normal/fault/test全量與released比較 |
| 0C-11 TS2Vec | 600epochs訓練完成，下游未完成 | service／Metric+Trace+Log、seed405、320dims、batch32、lr0.001；耗時3162秒，checkpoint已存。test adservice shape1440×320且finite；與released MAE0.2264。全序列encoding及下游比較待完成；單序列差異不能代表RCA效果 |

2026-10-04 清理：移除零IQR標準差fallback函式、CLI與各入口設定。保留stored percentile clipping，零IQR用原始座標；非零median邊界已納入回歸檢查。既有歷史run artifacts保持原樣，不能把舊checkpoint視為移除fallback後的結果。實驗不增加權重載入要求。原始reproduction status仍唯讀。

移除fallback後本機測試73項全部通過（刪除2項專測fallback的測試，新增零IQR且median非零的裁切檢查）；依使用者指示排除1項需要Windows DPAPI的憑證加密測試，不執行網路推論測試。TS2Vec的max_threads設定會import mkl-service而引入第二份OpenMP runtime，本runner改由Torch直接設定threads，未使用KMP_DUPLICATE_LIB_OK繞過衝突。

已知需正常使用者權限：OAuth 網路及 DPAPI、含 DPAPI 的 unittest。GPU probe 可在沙箱完成，訓練與本機資料處理優先在沙箱執行。本機執行採 `uv run --no-sync`，不呼叫 Activate.ps1。

若後續授權未取得，記錄動作、時間、原因並跳過依賴工作；不將未回應視為同意。系統強制等待的權限視窗可能無法在30秒取消，屆時不得宣稱已跳過。

OAuth 呼叫失敗會停止全量 runner，避免對所有案例重複失敗請求。尚未實作自動重新登入，避免離席時開啟需人工互動的流程。

Dataset 更新不執行原始 `update_dataset.py` 中附帶的 random-labeling 副作用。fault type 數值對照與已知磁碟名稱正規化保留；非法型別、未知類別或漏標保留原 y/y_mask 並記錄，避免把格式錯誤當成 No Fault。JSON 擷取使用標準 decoder 找出完整 object，不全域替換 apostrophe。正式更新要求100案例完成；partial 模式僅供另目錄診斷，不能當作正式重現。


2026-10-04 恢復進度：使用者已恢復網路與DPAPI授權；Luna OAuth check通過（LUNA_OK），100cases runner已續跑。先前跳過網路的紀錄為歷史狀態。Raw Metric入口補上istio，2項相關測試通過；保留修正前pipeline status與log，重新執行raw metric及後续步驟。報告記錄公開入口與released中間檔不一致、作者可能分批改腳本執行的推測，以及僅istio標準化仍待數值核對的限制。
