# LasRCA 0C-06～11 結案核對

2026-10-05：六項已依使用者核准的實驗範圍完成。0C-07／08 原文指定 GPT-4，本次改用 GPT-6 Luna OAuth；因此結論是「核准的替代實驗完成」，不能寫成原 GPT-4 條件完全重現。原始 `reproduction_staus_original.md` 保持唯讀，其 Not started 欄位未修改。

本次補完 0C-10 的逐 script 輸入／輸出數量、計數單位及產物歸屬。沒有重新訓練，也沒有修改前處理結果。以下路徑均相對 `runs/lasrca`；詳細實驗結果見 [第一輪結果](one_round_results_20261004.md)，encoder 來源及追加對照見 [來源報告](encoder_public_provenance.md)。

## 原始要求逐項驗收

| 項目 | 已保存與核對的內容 | 具體證據 | 結論與界線 |
|---|---|---|---|
| 06 四階段 labeling | 原選樣 100 cases 的 first／second／third／summarization prompts、responses；解析後 fault type、實際 explanation；完成／格式／錯誤統計、模型、usage、成本 | `luna_20261004/labeling_report.json/.md`、`labels/{parsed_labels.json,explanations.json,validation_errors.json}`、`responses`、`usage/{request_associations.csv,request_usage.csv,summary.json,cost.json}`、`errors` | 100/100 摘要可解析，653 entity occurrences 中 640 合法、13 unknown。理由按實際 stage-3 case 層級保存，不編造逐 entity 理由。USD 0.66810344 為 API 等值估算；OAuth 實付不可得，失敗請求 usage 不推定為零。 |
| 07 更新與 retraining | 正式 k1 dataset；完整 y／y_mask 前後快照、逐 entity diff、新增標籤與分布、輸入不變檢查；405～409 五 seed 各 500 epochs，checkpoint／duration／logs | `luna_20261004/dataset/{k1_luna.pkl,labels_before.npz,labels_after.npz,label_changes.json,update_statistics.json,fault_type_distribution.csv,input_signature.json}`；`luna_k1_no_std/sweep_status.json` 及其五個 run 的 manifest／checkpoints／metrics／logs | 640 個 mask 0→1，13 unknown 不更新。跨 split 共用 label row 問題已修正並恢復完成；舊失敗仍保留。策略為 Luna。 |
| 08 k0／k1 比較 | 同 split／features／GT／seed／前處理配對；node／pod／service AC@1/3/5、Micro／Macro P/R/F1；逐 seed、mean±母體 std、絕對／相對差、論文提升方向與逐 entity predictions | `luna_k0_k1_comparison/{pairing_manifest.json,comparison.json,comparison.md,per_seed_comparison.csv,summary_comparison.csv,paper_comparison.json,paper_comparison.csv,paper_comparison.md}`；兩個 sweep 的 `prediction_verification` | 五 seed checkpoint 重評估的 12 指標一致。結果有升有降，非全面提升；Luna、額外 percentile clipping 與 Macro F1 定義差異另列。 |
| 09 錯誤分析 | 全 653 occurrences 核對；20 個不同故障案例的 entity、精確 GT locator、LLM label、完整原 response、taxonomy、正式 update impact 與數量分母 | `luna_20261004/audit/{errors.json,error_cases.csv,case_details.md,error_taxonomy.json,error_type_counts.csv,update_impact.jsonl,summary.json}` | 86 異常 entities、36 cases：73 合法錯標（漏判50／誤報16／類別錯7），13 unknown。正式更新影響已關聯，不再僅為 simulation；原因無證據者不指定 stage。 |
| 10 raw preprocessing | 抽樣與全量各十個 script 完成；逐檔／欄位數量與單位、schema、duration、失敗／中斷紀錄、final manifest；重建與 released shape／label／topology／三模態特徵對照 | `raw_full_20261004/{stage_script_summary.json,stage_count_summary.csv,stage_input_output_counts.csv,stage_counts.json,stage_schemas.json,stage_runs.jsonl,pipeline_status.json,evidence_failures.json,final_manifest.json,stage_accounting.md}`、`comparison`、`interruption_snapshot_20261004_154516` 及各 script logs；抽樣在 `raw_20261004` | 最後缺口已補：10 scripts 均有數字化 input/output measures，unknown producer=0。4714 windows、15 covered topology sets 無差；抽樣部分 Istio 數值及 Log 欄位順序仍有差，已記錄而非宣稱全量逐值相等。全量無獨立 failures.jsonl，不虛稱存在；inspection failures=[]，歷史中斷保留 snapshot／logs。 |
| 11 TS2Vec | 至少一組 service／8 Metric encoder，作者公開 processed input、seed／hyperparameters、600 epochs、loss curve、duration、checkpoint；150 序列 encoding、embedding 差異與同 split／labels 下游 RCA 比較 | `ts2vec_20261004/{input_manifest.json,loss.csv,loss_curve.png,loss_curve.pdf,timing.json,model.pkl}`、`ts2vec_downstream/{encoding_manifest.json,service_replaced.pkl}`、`encoder_pair_20261004/comparison.json/.csv/.md`；追加 `encoder_public_recheck_20261005` | seed405 與追加 seed406 均完成；下游固定 seed405、各500 epochs。作者包只有 embedding 與下游模型，沒有 TS2Vec 權重；两次自訓均用同 SHA256 的作者公開 processed 資料，不能把效果差異歸因於新 raw 資料。node／pod 沿用作者 embedding。 |

## 10：為何要修正計數與歸屬

旧表以檔案路徑推定產物來源時，15 份 `edge_index.pkl` 的 topology producer 未被辨認；Trace patterns 與統計、Log patterns 與選樣統計也有階段歸屬混淆。這會使某個 script 看似缺輸出，或把後續 script 的結果算到前一階段，因此不足以逐 script 驗收。現在依公開程式的讀寫位置修正：topology → `dao.topology_dao`；Trace patterns → `dao.trace_dao`，Trace 統計 → `service.trace_generator`；Log patterns／miner／Istio words → `dao.log_dao`，其他 Log 統計及選樣 → `service.log_generator`。

原始資料夾存在未被設定選取的 CSV；把整個資料夾檔案數當作每個 script 讀取量會高估輸入。現在只列設定內 date/cloud、實際選用 metric 名稱與指定 Trace／Log CSV。node／service loader 的 `glob(...)[0]` 依現存資料夾順序推定；歷史沒有逐次 I/O tracing，因此這是來源程式與保留產物重建的「唯一依賴檔案／內容數量」，不是每次重讀次數或歷史讀取順序的直接量測。同階段重新讀取自身產物亦列為 input，每個檔案只算一次。設定檔明列為 input，topology 不虛構 raw 觀測列。

全量各 script 摘要如下；檔案數不能代替內容數量，內容數量完整列於 `stage_count_summary.csv`，每個 field 的計數／schema／路徑則在 `stage_input_output_counts.csv`。

| Script | 輸入檔 | 輸出檔 | duration 秒 | exit |
|---|---:|---:|---:|---:|
| dao.topology_dao | 18 | 15 | 0.265 | 0 |
| service.ent_edge_index_generator | 18 | 1 | 0.719 | 0 |
| service.time_interval_label_generator | 16 | 6 | 3.078 | 0 |
| dao.metric_dao | 408 | 1440 | 7222.297 | 0 |
| service.metric_generator | 1445 | 2 | 1395.562 | 0 |
| dao.trace_dao | 34 | 16 | 3359.813 | 0 |
| service.trace_generator | 21 | 3 | 317.484 | 0 |
| dao.log_dao | 21 | 33 | 11628.828 | 0 |
| service.log_generator | 43 | 9 | 39.469 | 0 |
| service.dataset_generator | 1447 | 1 | 7.109 | 0 |

例如，15 份 topology 輸出共 **2460 stored directed edges**，而非把 `[2,E]` 的 endpoint 索引算成兩倍邊數。window size 9 輸出為 **4714 時間窗、4714 label vectors、263984 entity label values**；不同 window sizes 各自統計，不把重疊窗口相加冒稱案例數。final dataset 有 **1,209,600 processed entity-minute observation rows／44,582,400 feature cells**，另保存同量 raw 欄位；兩者分列而非混成雙倍案例數。final metadata 的 **7380 stored edges** 包含其儲存結構中的重複引用，不能解讀成 7380 條唯一拓樸邊。

全量 manifest 原 5187 artifacts，加 4 份明確 configuration inputs 後為 **5191**；抽樣原713，現在 **717**。新增的是計數證據，非新增實驗案例。全量 83732、抽樣48245 列 field measures 是逐 script／input-output／field 的統計表列數，不能當作故障案例數。舊表保留於各 run 的 `accounting_before_correction_20261005`；本次核對 retained artifact hashes 與備份一致，未改資料結果。

修正工具 `experiments.raw_accounting` 的8項相關 unittest 通過，涵蓋產物來源、未選取 CSV、CSV records、rows／cells、edges、windows／labels，以及巢狀 mapping 不重複加總。code commit：`ec4be41`。計數工具、來源核對、hash、備份、恢復及監控皆是**與論文演算法無關的執行支援／重現驗證**。

## 結案後仍成立的限制

六項的執行與保存要求完成，不表示所有結果相等或所有差異原因已證實。OAuth 實付、歷史失敗請求 usage／HTTP／時間與未獨立量測的耗時維持不可得或 null；不補造。test GT JSON→CSV 的格式補齊有無損對照，作者可能手動改腳本的說法仍是推測。

raw pod 六項 Istio 數值差異、Log 欄位順序、公開程式 fit/split 邊界與零值分支修正均已披露。追加 encoder 僅兩個 encoder seeds、單一固定下游 seed，作者 encoder seed／權重未知；不宣稱五 seed 穩定性或找出全部差異根因。詳細 V-01～20 的檢查結果包含「已核對但發現差異／限制」，不是把所有假設都當成成立；GT 僅供離線 audit，不回填修正 Luna labels。

上述限制不要求額外重訓才能滿足本轮的原始「比較、記錄」目標。人工驗收可以根據保存結果進行；新的全量逐值比較、差異根因實驗或增加 encoder seeds 屬另行定義的研究範圍。

原始進度文件 SHA256：`9F6251D901534C47E8CC2059DB8B1E27BFAC8F9CD98775F88AF775AA73E0B0F0`。
