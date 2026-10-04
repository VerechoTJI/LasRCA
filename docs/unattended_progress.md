# LasRCA 工作紀錄（2026-10-04）

## 最終一輪核對（23:14）

六項均已實際完成一輪；最後全量raw證據於22:37完成。最新classifiers在recovery controller為completed，原controller的preprocessing／encoder為completed；已處理的舊classifiers failed保留為歷史。100cases、640合法新增labels、五seed各500epochs、全部checkpoint hash／paired input及prediction重算已驗證。全量raw十stage exit0，5187artifacts、0inspection failures，4714windows／15topologies皆0差異。150service encodings與單seed兩組下游完成。

結果及验收限制完整寫於[第一輪結果](one_round_results_20261004.md)。三類F1提高、Precision下降，node定位下降；raw抽樣234feature rows中pod六列Istio數值不同、Log欄位順序不同，不聲稱全面數值一致。20個錯誤案例詳解已連正式更新，86個entity錯誤包含73個合法錯標與13個unknown。尚待人工验收及六個Istio差異原因核對，不再有需等待的本輪背景實驗。原始status hash保持不變，完成提醒在產物核對後停止。

## 21:18監控：100cases完成，資料更新攔截已修復並恢復重訓

Luna100cases四階段於20:52前全部完成，100摘要可解析；653個entity occurrences中640個類別合法、13個unknown_fault。正式更新只採640個合法labels，13個保留原y／mask，不以No fault或GT替代。原始回答、完整parsed evidence、usage及歷史錯誤保留。

20:52正式builder失敗：輸入保護發現train_valid/y改變，尚未寫k1_luna.pkl。不是檢查誤判，也不是quota再次耗盡。公開prepared cache的train_valid及unlabeled共用同一批label row物件；整個dataset deepcopy保留alias，因此更新unlabeled連帶改到32個train_valid標籤row。只deepcopy本身並無差異，真正更新才改變protected_labels hash。診斷保存`luna_20261004/errors/signature_diagnosis.json`，失敗stdout/stderr/manifest保留於原controller execution，不覆寫。

修正：更新前獨立複製unlabeled y／y_mask，逐list row解除跨split及同split alias；特徵、切分、GT、其他split均保持不變。共享row回歸測試與dataset／pairing相關8tests通過，commit c3949b3。這是本次dataset更新工具的正確性修正，與論文演算法無關，不能稱作者刻意設計或根據GT修正Luna輸出。

正式dataset已成功產生，640labels均mask0→1。source SHA256 `c47c557e732f0d1c33e765a1ea97a5146f5f6c918df876d4bff2ec80e1975ab5`；target `6e42fe9cfd49a5ad5173449bdb5001dcfd83c4743554a1d666efa86ca89cb3d8`。完整before/after y／mask、分布、label_changes與input_signature已保存；features／split／protected labels三項hash全相同，checks_passed=true。

僅重啟失敗的classifiers leg：新controller `round_followup_recovery_20261004`，21:16:58開始k1 seed405；原`round_followup_20261004`仍跑全量Log，encoder已完成，不重複啟動。原controller classifiers failed保留為歷史，監控讀recovery的最新classifiers狀態。每小時提醒已更新此規則，以免將已處理的失敗重複通知。尚未宣稱k1五seed／整輪完成。

## 最新恢復檢查（16:45；以下15:48及更早紀錄保留為歷史）

Quota重設後已實際恢復，而非僅檢查可恢復性。當時本機舊processes與sessions均已消失，沒有可用exit code，不能斷言全部由quota中止。

| 任務 | 本次核實結果 | 下一步／限制 |
|---|---|---|
| 06 | Luna OAuth check通過；case44第二階段從成功request快取恢復；目前36／100 cases四階段完成，runner仍在執行 | 保留成功回答，繼續剩餘案例；尚不能當作全量標註完成 |
| 07 | 尚未開始正式100cases的dataset更新及k1五seed；controller等待06 | 全量後自動更新與重訓，不使用partial dataset冒充正式結果 |
| 08 | k0 seeds405～409各500epochs全部完成；五個checkpoint保留，重評估12指標均與原訓練一致 | k1完成後核對paired inputs並輸出差值／論文方向；k0不重訓 |
| 09 | 已有部分完成案例的GT定位、分類與10個不同錯誤案例詳細因果核對 | 等100cases及正式dataset再核對實際更新影響，當前為simulation |
| 10 | 抽樣十個stage全部exit0；713個artifact counts/schema掃描完成、0個inspection failures；1428時間窗label及2拓樸0差異。final dataset與released特徵／shape比較已產生。全量保留前三stage，從Metric DAO恢復且仍在執行 | 全量Metric完成後接Trace、Log、組裝和完整證據；抽樣Log缺9欄原因需全量fit核對 |
| 11 | 600epochs checkpoint保留；150service序列全部重新編碼成功（3225.64秒），兩組下游seed405各500epochs及比較均完成 | 本輪單seed、service encoder部分替換驗證完成，不能宣稱三類encoder均自訓或五seed穩定性 |

11結果：service AC@1為0.340909→0.352273（+1.14百分點）、AC@5為0.681818→0.727273（+4.55百分點）；node／pod AC@1分別下降2.99／1.16百分點。service Macro F1為0.016335→0.016073，並非全面提升。僅替換service embedding仍可經圖模型及重新訓練影響其他entity預測；兩組split／labels相同，但僅一seed，不能推論穩定性或論文整體效能。

抽樣pod為1440×38，released為1440×47：本次抽樣fit沒有選出Log features，released有9個。兩日期的抽樣node／service／pod timestamps全部1440點對齊；無Log共同欄位的數值比較明列「no_shared_features」，不當作一致。可能與抽樣fit範圍／Log pattern threshold相關，待全量fit核對，不能先判定作者資料缺失。

本次Log停止原因：`calculate_word_tf_idf()`對前一步Log DAO已建立的`analysis/log`再次不帶exist_ok建立目錄，引發FileExistsError；並非只在重跑時發生。修正為exist_ok=True，不改TF-IDF或特徵選擇公式。失敗log／status另存`raw_20261004/log_generator_failure_20261004_1630`（目錄名非精確失敗時間，實際時間以pipeline_status／stage_runs為準），完成Log DAO不重跑。此為與論文演算法無關的執行修正。

證據：`round_followup_20261004/status.json`的encoder leg已completed；`encoder_pair_20261004/comparison.json/.csv/.md`含完整兩組protocol、embedding／dataset／checkpoint hash及36指標；`ts2vec_downstream/encoding_manifest.json`含150序列coverage與encoding設定；`raw_20261004/comparison`有shapes、feature_coverage、feature_summary、feature_samples與metadata核對。執行中的controller會等待其餘前置結果後接續，不將waiting_or_running當作完成。

本次完成並獨立提交：beac4de（具體label flow與CSV證據）、365fdd7（Log目錄修正及回歸）、81f76f4（缺少／未共同特徵與timestamps覆蓋）。相關10＋3項本機測試通過。原始status SHA256仍為`9F6251D901534C47E8CC2059DB8B1E27BFAC8F9CD98775F88AF775AA73E0B0F0`，未修改。

## 15:48執行快照（歷史）

使用者授權繼續跑完六項的一輪實驗後，再統一驗收比較。網路與DPAPI可用；原始進度文件仍唯讀。每個獨立程式任務已測試並commit，執行中不把工具完成稱為實驗完成。

| 任務 | 已完成的實際證據 | 尚待完成 |
|---|---|---|
| 06 | Luna至少22／100 cases四階段完成；重設quota後OAuth check為LUNA_OK，case44已從快取續跑完成 | 全100、最終格式／用量／成本統計。OAuth實際方案費用不可由API牌價推定，仍標不可得 |
| 07 | 完整before／after y／mask、fault分布及原始特徵／split保護已實作並測試 | 正式100cases dataset、k1五seed各500epochs |
| 08 | 移除std fallback的k0已完成405～409，每seed500epochs；五份checkpoint hash已驗證。evaluation_five_seed已保存真正跨五seed的mean±std，舊每run摘要另保留 | k1、成對來源核對、逐seed prediction補匯出與論文方向表 |
| 09 | 20cases／120 entity occurrences離線核對，15個entity標籤不符或格式異常；案例時間locator已由來源索引、全部標籤與觀測內容驗證 | 全100分析、10～20例詳細因果檢查與正式更新影響核對 |
| 10 | 全量raw inputs已備齊；test原始JSON Ground Truth無損轉5份CSV、241cases。全量4714時間窗label、15拓樸與released均無差異 | 抽樣Log／組裝與修正後Metric重跑；全量Metric／Trace／Log／組裝、counts／schema／特徵對照 |
| 11 | service TS2Vec seed405、600epochs已完成；實際8個Metric輸入。released下游seed405、500epochs及分類／定位完成，duration145.3秒 | 所有150service序列encoding、替換後下游、成對比較及loss圖。node／pod維持released，須明列部分替換 |

Raw已確認兩個來源差異：公開Metric入口沒有呼叫Istio產生器；generator只啟用Istio標準化，而released node等結果已標準化。已恢復既有四種resource類別處理。另確認全NaN HTTP統計分支沿用上一個GRPC特徵，released也出現對應複製值；改為明確零值會改變raw重建特徵，屬數值修正差異，不能聲稱完全相同。Luna主線使用released processed inputs，此raw修正不影響k0／k1成對訓練輸入。

各run：`runs/lasrca/luna_20261004`、`baseline_no_std`、`raw_20261004`、`raw_full_20261004`、`ts2vec_20261004`、`ts2vec_downstream`、`encoder_pair_20261004`。API failure code只保存安全識別碼，不保存SDK的潛在憑證訊息；執行中的舊runner在下次啟動才使用新失敗分類。

Quota恢復檢查：舊session／local processes不再存在，未完成階段無有效exit code，原因不臆測。各run已保存interruption_snapshot及檔案清單，統一檢查紀錄在`runs/lasrca/recovery_20261004_154516/inspection.json`。保留600epochs encoder及全部已完成k0 checkpoints；Luna成功requests重用。抽樣Metric需重跑四類標準化（修正前all_metric.pkl已另存），Log重跑中斷階段；全量保留前三stage、從Metric DAO重跑。編碼尚無完成檔，需重新encoding。15:46本機回歸94 tests全數通過，包含DPAPI；未更動原始進度文件。

## 歷史紀錄

16:10補充：五seed checkpoint重評估已完成，全部12指標與原訓練紀錄一致；逐entity predictions／GT及ranking保存於`baseline_no_std/prediction_verification`。TS2Vec `input_manifest.json`記實際8個Metric、全部150序列、完整source defaults與fit/test界線；`loss_curve.png`／`.pdf`已輸出並檢查。錯誤分析已有10個不同案例的完整stage3原文與更新影響，惟仍為25cases快照、未更新正式dataset。已啟動`round_followup_20261004`，等待前置成果後依序完成k1／比較、full raw後段與證據、自訓encoder下游；此controller屬與論文無關的執行支援。原始碼／PDF原表已核對；分類方向不能把Precision下降誤說成提升。

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
