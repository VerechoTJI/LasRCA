# LasRCA 工作紀錄（2026-10-04）

`E:/Misc/FastCodingWorkspace/AI/SMCI/reproduction_staus_original.md` 唯讀，所有進度另存本檔。沿用公開 100 cases/subgraphs，不另作選樣對照。模型為 GPT-6 Luna OAuth。

每完成一個獨立可驗收的程式任務，通過相關測試後提交一次。實驗執行結果另記，不能把 runner 完成視為實驗完成。

| 任務 | 狀態 | 證據／限制 |
|---|---|---|
| OAuth 接入 | 完成；commit 69db66d | case 6 四階段實際驗證；65 tests |
| 06 runner、續跑與 UTF-8 | 程式完成 | 68 tests；case 0 完整實驗仍在執行。成功請求以 model + prompt hash 保存並續用；失敗請求不快取 |
| 06 全量 | 待單案例執行完成後啟動 | runs/lasrca/luna_20261004；公開選樣100案例 |
| 07 Dataset／重訓 | 待執行 | 原始 k=1 程式是重新初始化後訓練，不是載入 k=0；本工作保留原始語義，修正先前計畫中的錯誤假設 |
| 08／09 | 等待 LLM 結果與 k=1 | 不預設模型品質改善 |
| 10／11 | 待執行 | raw archives 已存在；GPU 在沙箱可用 |

已知需正常使用者權限：OAuth 網路及 DPAPI、含 DPAPI 的 unittest。GPU probe 可在沙箱完成，訓練與本機資料處理優先在沙箱執行。啟用 venv 後使用 `python -m ...` 以便授權固定模組範圍。

若後續授權未取得，記錄動作、時間、原因並跳過依賴工作；不將未回應視為同意。系統強制等待的權限視窗可能無法在30秒取消，屆時不得宣稱已跳過。

OAuth 呼叫失敗會停止全量 runner，避免對所有案例重複失敗請求。尚未實作自動重新登入，避免離席時開啟需人工互動的流程。
