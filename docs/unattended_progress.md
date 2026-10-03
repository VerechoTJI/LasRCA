# LasRCA 工作紀錄（2026-10-04）

## 權限請求失敗

使用者後續指示：先跳過全部網路與 DPAPI 操作。已停止全量 Luna runner（session 69295，Ctrl-C 結束）；完成案例為0與5，正式100案例未完成。06全量、正式07訓練與08／09完整實驗結果等待恢復網路授權；可繼續本機實作、測試、raw preprocessing 與 TS2Vec。改用 `uv run --no-sync --cache-dir ../out/uv-cache python ...`，不呼叫 Activate.ps1。

2026-10-04：為避免每次重新啟用 venv，建立正常使用者權限的持續 PowerShell（session 24409）。建立成功，但第一次後續 `write_stdin` 輸入即被工具拒絕，訊息為 `rejected by user`。Python 路徑檢查、檔案試跑、OAuth check 均未在該次工具呼叫中確認執行。停止重試此 session；此路線尚未證明可免除後續授權。原有沙箱持續 shell 的 venv／CUDA／5 tests 已驗證成功；先前單獨授權的100案例標註 session 69295 已啟動，但目前不得聲稱全量完成。

`E:/Misc/FastCodingWorkspace/AI/SMCI/reproduction_staus_original.md` 唯讀，所有進度另存本檔。沿用公開 100 cases/subgraphs，不另作選樣對照。模型為 GPT-6 Luna OAuth。

每完成一個獨立可驗收的程式任務，通過相關測試後提交一次。實驗執行結果另記，不能把 runner 完成視為實驗完成。

| 任務 | 狀態 | 證據／限制 |
|---|---|---|
| OAuth 接入 | 完成；commit 69db66d | case 6 四階段實際驗證；65 tests |
| 06 runner、續跑與 UTF-8 | 程式完成 | 68 tests；case 0 完整實驗仍在執行。成功請求以 model + prompt hash 保存並續用；失敗請求不快取 |
| 06 全量 | 待單案例執行完成後啟動 | runs/lasrca/luna_20261004；公開選樣100案例 |
| 07 Dataset／重訓 | 待執行 | 原始 k=1 程式是重新初始化後訓練，不是載入 k=0；本工作保留原始語義，修正先前計畫中的錯誤假設 |
| 07-A Dataset 更新及隔離輸入 | 程式完成，正式更新等待100案例 | 單元測試驗證只改選中 unlabeled 的 y/y_mask；test split 不變；16項相關測試通過。`llm.build_labeled_dataset` 與 `--prepared_dataset_path` 避免覆寫 released caches |
| 08／09 | 等待 LLM 結果與 k=1 | 不預設模型品質改善 |
| 08 比較工具 | 程式完成 | 2 tests：成對seed/metric檢查、GT一致性、母體std、baseline零的相對差。正式結果等待完整補標及5 seeds重訓 |
| 10／11 | 待執行 | raw archives 已存在；GPU 在沙箱可用 |

已知需正常使用者權限：OAuth 網路及 DPAPI、含 DPAPI 的 unittest。GPU probe 可在沙箱完成，訓練與本機資料處理優先在沙箱執行。啟用 venv 後使用 `python -m ...` 以便授權固定模組範圍。

若後續授權未取得，記錄動作、時間、原因並跳過依賴工作；不將未回應視為同意。系統強制等待的權限視窗可能無法在30秒取消，屆時不得宣稱已跳過。

OAuth 呼叫失敗會停止全量 runner，避免對所有案例重複失敗請求。尚未實作自動重新登入，避免離席時開啟需人工互動的流程。

Dataset 更新不執行原始 `update_dataset.py` 中附帶的 random-labeling 副作用。fault type 數值對照與已知磁碟名稱正規化保留；非法型別、未知類別或漏標保留原 y/y_mask 並記錄，避免把格式錯誤當成 No Fault。JSON 擷取使用標準 decoder 找出完整 object，不全域替換 apostrophe。正式更新要求100案例完成；partial 模式僅供另目錄診斷，不能當作正式重現。
