# LasRCA 後六項任務介紹與結果草稿 v2

2026-10-11。依 [簡報歸納原則](task_introduction_principles_20261011.md) 撰寫，涵蓋0C-06～11。每項保留「介紹正文」，新增「結果正文」，講稿備註交代必要性、名詞、來源及解讀限制。第一版保留於six_tasks_introduction_draft_20261011.md。這是完整文字草稿，尚未決定一頁放多少內容，也未將技術細節從正文刪除。實驗已按核准範圍完成，以下目標與要求用於介紹工作，不代表要再執行一輪。

沿用公開程式的100 cases／subgraphs；LLM採使用者核准的GPT-6 Luna OAuth，原07／08的GPT-4條件因此有替代設定差異。原始進度文件與PPTX均未修改。OAuth與新增紀錄／恢復功能屬與論文演算法無關的執行支援。

## 0C-06 Labeling Method Verification｜LLM標註流程驗證

### 介紹正文

**目標**

- 確認所選故障案例能完成四階段LLM分析，取得可供分類器使用的entity故障類型標籤。
- 檢查回答能否解析、名稱與故障類型是否合法，並保存模型判斷的實際理由。
- 記錄執行錯誤、模型版本、token用量及成本，說明此次標註的完成範圍。

**要求**

- 沿用已選出的100個cases／subgraphs，逐案例保存first、second、third及summarization的完整prompt與response。
- first按node／pod的Metric類別分析，second整合同一entity的判斷，third結合子圖關係分析，summarization整理為entity名稱與`exact_fault_type`。
- 保存解析標籤及stage-3的實際explanation，分別統計案例完成率、格式異常及合法entity labels數。
- 記錄每個請求的requested／returned model、usage與API／路徑錯誤。成本估算須標明計算依據，OAuth實付不可得時明列不可得。

**程式變更**

- 以OAuth接入GPT-6 Luna，保持公開程式四階段流程與prompt語義。這是模型與呼叫方式的替代設定，不代表原GPT-4結果重現。
- 新增請求與案例／階段的關聯、原文保存、格式驗證及中斷恢復，讓錯誤與成功產物可追查。上述功能屬執行支援，與論文演算法無關。

### 結果正文

| 驗證項目 | 本輪結果 |
|---|---|
| 四階段完成 | 100／100 cases，完成率100%；各階段prompt與response已保存 |
| 摘要解析 | 100／100可解析，JSON parse errors=0 |
| Entity labels | 653 occurrences，640合法（98.01%）、13 unknown（1.99%） |
| 模型版本 | 2479筆成功unique requests的returned model均為gpt-6-luna |
| Token用量 | Input 3,801,843，output 737,533，total 4,539,376；成功請求usage無缺漏 |
| 成本 | API牌價等值估算USD0.66810344；OAuth實付不可得 |
| 執行錯誤 | 記錄到1次歷史OAuth／API失敗，後續恢復；目前failed／pending cases皆0 |
| Explanation | 保存完整stage-3 case層級理由與來源，不額外生成逐entity理由 |

**結果解讀**：四階段可正常走完，取得640個可供更新的標籤。合法率衡量名稱與格式是否可用，不是標籤正確率，正確性另由09核對。快取重用不算新請求，歷史失敗attempt記錄不完整，無法將1次當成全部失敗數；失敗請求的token用量也不推定為零。

**資料範圍**：LLM直接分析node／pod的Metric，第三階段加入子圖entity與關係；沒有直接讀取Trace／Log。Service標籤可由第三階段案例分析產生。

### 講稿備註

頁面目的：交代LLM回答如何成為下一項訓練的輸入。entity是待判斷的node、pod或service；subgraph是該案例選取的entities及其關係。prompt是實際送給模型的提示內容，response是模型回答；`exact_fault_type`是摘要中待解析的故障名稱。OAuth是帳號授權呼叫方式，token是服務回報的輸入／輸出文字計量單位。

因為一句自然語言判斷還不能直接填入訓練資料，流程先按Metric類別分析node／pod，再合併同一entity的判斷。第三階段才結合子圖中的entities及關係，形成案例層級的判斷與理由，可涵蓋service。摘要階段將回答整理成固定格式，程式再檢查entity是否存在、故障名稱是否在合法集合內。不同stage請求數並不相同，不能用100 cases推定只有400次請求。GT不新增至prompt，也不用來修正回答。

本輪100/100案例摘要可解析，653 entity occurrences中640合法、13 unknown。occurrence指「某案例中的某entity」，同一entity出現在不同案例須分開計數。100%的案例解析完成率不表示標籤全對。第三階段理由按實際case層級保存，不編造逐entity explanation。

證據：`runs/lasrca/luna_20261004/labeling_report.json`、`labels/{parsed_labels.json,explanations.json,validation_errors.json}`、`prompts`、`responses`、`usage/{request_usage.csv,cost.json}`、`errors`。四階段對象與流程依 `docs/remaining_six_tasks.md` 的四階段表、`code/llm/run_labeling.py` 及其實際呼叫的公開labeling程式核對。API等值成本約USD0.6681，實際OAuth費用不可得。

銜接：合法回答能進入資料更新，但還需確認更新範圍及訓練是否成功。

## 0C-07 Classifier Retraining｜補標後的分類器重訓

### 介紹正文

**目標**

- 將LLM產生的合法標籤加入訓練資料，確認新增監督資訊能用於small classifier重訓。
- 檢查資料更新僅影響所選未標註entities，保留原始特徵、拓樸及評估資料。
- 使用五組seed完成k=1訓練，保存每次實際讀取的資料與模型，供前後比較。

**要求**

- 保存更新前後的完整`y`／`y_mask`、逐entity變更、新增label數及fault-type分布。
- 未知／無法解析的標籤保留原`y`／`y_mask`，記錄忽略原因，不能自動填成No fault。
- 核對features、split、topology及受保護labels不變，明確記錄新增標籤的範圍。
- 固定seeds405～409，每組完成500 epochs；保存dataset來源、訓練設定、checkpoint及SHA-256、loss、duration與完整log。

**程式變更**

- 新增標籤快照、分布與全資料差異核對，讓每個新增標籤都能追到LLM原回答。這些是與論文演算法無關的保存／驗證功能。
- 修正跨split共用label row的問題，更新前建立獨立可寫的label列，避免train更新連帶改到其他split。
- 沿用已移除標準差fallback的訓練路徑，保留Trace IQR=0時的第1／99百分位clipping。clipping是本次與公開原路徑的數值處理差異，兩組比較須一致。

### 結果正文

正式dataset已產生：640個mask由0變1，73個y值改變，13個unknown保留原值；已核對原features、split及受保護labels不變。73是更新前後類別值不同的數量，不是新增label數，與640不能相加。

| Seed | Completed epochs | 最後total loss | Run duration秒 | Checkpoint |
|---|---:|---:|---:|---|
| 405 | 500 | 0.184366 | 342.015 | model_seed_405_k_1_Luna.pkl |
| 406 | 500 | 0.096405 | 296.531 | model_seed_406_k_1_Luna.pkl |
| 407 | 500 | 0.043164 | 283.797 | model_seed_407_k_1_Luna.pkl |
| 408 | 500 | 0.137405 | 287.031 | model_seed_408_k_1_Luna.pkl |
| 409 | 500 | 0.198918 | 281.016 | model_seed_409_k_1_Luna.pkl |

五seed均完成500 epochs，checkpoint SHA-256、設定與完整history已保存。表中loss取history最後一列total_loss，epoch使用程式的0起算索引（最後499）；duration取training_summary.duration_seconds，屬run量測，不另推定純optimizer時間。Loss衡量訓練目標，不代表測試成效。

**問題及處理**：跨split共用label row曾使更新越界，保護檢查攔下後修正，重新生成正式資料並完成訓練。舊失敗保留，結果採恢復後的run。

**Log的使用**：label更新本身讀LLM摘要，不讀Log；後續small classifier的pod輸入仍包含Metric／Trace／Log數值特徵，node／service只用Metric。

**具體產物**：k1_luna.pkl及前後NPZ快照、label_changes.json、fault_type_distribution.csv、五組checkpoint／training_history；實際訓練輸入為manifest的prepared_dataset_path。

### 講稿備註

頁面目的：區分「模型產生標籤」與「標籤正確進入訓練」。`y`保存故障類別，`y_mask`表示該位置是否有可用監督標籤。mask由0變1代表新增可用標籤，即使類別是No fault也應計入。split是程式使用的資料分組／索引，seed是固定隨機過程的設定，epoch是一次訓練循環，checkpoint是保存的模型參數，SHA-256用來辨認檔案版本。

本輪先將640個合法標籤更新到所選位置，13個unknown不更新。完整前後快照與差異核對能確認labels流向，避免用少量抽查漏掉其他split的變動。實際遇到共用label row造成更新越界，保護檢查攔下後修正，才生成正式dataset並完成五seed訓練。這個修正是讓更新符合既定範圍，沒有用GT把LLM錯標改成正解。

k=0表示補標前，k=1表示本輪補標後。這裡「重訓」只交代實際dataset與500 epochs設定，不額外聲稱論文要求特定接續訓練方式。IQR是中間50%數值的範圍，clipping是限制極端數值的處理；此設定及其影響須與k0對照共同記錄。

證據：`luna_20261004/dataset/{labels_before.npz,labels_after.npz,label_changes.json,input_signature.json,update_statistics.json,fault_type_distribution.csv}`、`luna_k1_no_std/sweep_status.json`所指五個run的manifest／checkpoints／training history。此處及以下run路徑均相對 `runs/lasrca`。

銜接：五組模型都完成，只能證明可訓練，效果是否改變須用相同條件比較。

## 0C-08 Retrained Classifier Evaluation Comparison｜補標前後成效比較

### 介紹正文

**目標**

- 比較補標前k=0與Luna補標後k=1的故障定位及分類效果。
- 固定資料與訓練條件，讓前後差異可以對應到本輪標籤更新。
- 比較五seed結果與論文提升方向，說明提升、下降及設定差異。

**要求**

- k0／k1配對使用相同features、split、GT、前處理及seeds405～409，兩組各500 epochs。
- 對node、pod、service回報AC@1／3／5，以及Micro／Macro Precision、Recall、F1。
- 保存逐seed結果及mean ± std，明列std採五seed的母體標準差。
- 回報絕對差與相對差，標明百分點或相對百分比；基準為0時相對差列不可計算。
- 保存逐entity probability、GT及案例ranking以供重算，與論文對應表格逐項比較方向及條件。

**程式變更**

- 新增輸入配對核對、checkpoint重評估與逐案例預測匯出，確認比較使用實際完成的模型。
- 新增逐seed／統計摘要及論文方向表。以上是與論文演算法無關的評估與保存功能。

### 結果正文

k0／k1各五seed、各500 epochs，使用相同features、split、GT與前處理。每格按A／Service、B／Pod、C／Node排列。k0與k1為百分比的mean ± 母體std；提升大小保留正負號，負值表示下降，並非所有指標都提升。

| Metric | k0（A／Service、B／Pod、C／Node） | k1（A／Service、B／Pod、C／Node） | 該指標提升大小（絕對／相對） | 論文該指標提升大小（絕對／相對） |
|---|---|---|---|---|
| AC@1 | A：78.86 ± 5.31%<br>B：56.28 ± 6.31%<br>C：79.40 ± 5.20% | A：79.55 ± 4.87%<br>B：58.37 ± 6.80%<br>C：76.42 ± 5.93% | A：+0.68 pp／+0.86%<br>B：+2.09 pp／+3.72%<br>C：-2.99 pp／-3.76% | A：不可計算／不可計算<br>B：不可計算／不可計算<br>C：不可計算／不可計算 |
| AC@3 | A：86.82 ± 3.18%<br>B：67.21 ± 4.38%<br>C：89.55 ± 1.89% | A：89.77 ± 2.87%<br>B：70.23 ± 4.63%<br>C：88.06 ± 4.43% | A：+2.95 pp／+3.40%<br>B：+3.02 pp／+4.50%<br>C：-1.49 pp／-1.67% | A：不可計算／不可計算<br>B：不可計算／不可計算<br>C：不可計算／不可計算 |
| AC@5 | A：92.27 ± 3.76%<br>B：71.16 ± 3.71%<br>C：92.54 ± 2.50% | A：92.50 ± 2.93%<br>B：76.51 ± 2.00%<br>C：90.45 ± 3.96% | A：+0.23 pp／+0.25%<br>B：+5.35 pp／+7.52%<br>C：-2.09 pp／-2.26% | A：不可計算／不可計算<br>B：不可計算／不可計算<br>C：不可計算／不可計算 |
| Micro Precision | A：75.37 ± 6.91%<br>B：77.47 ± 5.42%<br>C：58.48 ± 1.73% | A：66.85 ± 10.55%<br>B：66.45 ± 1.60%<br>C：47.84 ± 7.10% | A：-8.52 pp／-11.30%<br>B：-11.03 pp／-14.23%<br>C：-10.64 pp／-18.19% | A：-19.26 pp／-25.64%<br>B：-38.81 pp／-48.95%<br>C：+11.26 pp／+20.62% |
| Micro Recall | A：26.36 ± 3.17%<br>B：28.31 ± 1.84%<br>C：26.87 ± 3.13% | A：46.82 ± 2.43%<br>B：50.14 ± 2.10%<br>C：42.09 ± 2.57% | A：+20.45 pp／+77.59%<br>B：+21.83 pp／+77.10%<br>C：+15.22 pp／+56.67% | A：+27.50 pp／+119.83%<br>B：+38.17 pp／+139.56%<br>C：+17.91 pp／+70.60% |
| Micro F1 | A：39.00 ± 4.16%<br>B：41.36 ± 1.75%<br>C：36.70 ± 3.12% | A：54.49 ± 2.52%<br>B：57.09 ± 0.81%<br>C：44.51 ± 3.42% | A：+15.48 pp／+39.70%<br>B：+15.73 pp／+38.04%<br>C：+7.80 pp／+21.27% | A：+17.45 pp／+49.87%<br>B：+9.11 pp／+22.43%<br>C：+17.84 pp／+52.29% |
| Macro Precision | A：64.26 ± 8.11%<br>B：77.52 ± 2.29%<br>C：69.10 ± 1.33% | A：59.63 ± 4.48%<br>B：71.45 ± 4.98%<br>C：56.97 ± 9.61% | A：-4.63 pp／-7.21%<br>B：-6.07 pp／-7.83%<br>C：-12.13 pp／-17.56% | A：-4.17 pp／-6.86%<br>B：-24.81 pp／-32.63%<br>C：+5.04 pp／+7.37% |
| Macro Recall | A：29.20 ± 3.24%<br>B：30.96 ± 1.71%<br>C：28.43 ± 3.49% | A：53.42 ± 3.14%<br>B：54.56 ± 1.98%<br>C：39.07 ± 2.05% | A：+24.22 pp／+82.96%<br>B：+23.59 pp／+76.20%<br>C：+10.64 pp／+37.44% | A：+30.16 pp／+122.35%<br>B：+38.10 pp／+128.02%<br>C：+14.31 pp／+52.94% |
| Macro F1 | A：36.19 ± 3.41%<br>B：40.14 ± 1.74%<br>C：36.01 ± 3.48% | A：51.76 ± 2.90%<br>B：56.22 ± 0.97%<br>C：41.05 ± 3.26% | A：+15.57 pp／+43.03%<br>B：+16.08 pp／+40.05%<br>C：+5.04 pp／+14.01% | A：+21.06 pp／+65.53%<br>B：+18.21 pp／+47.02%<br>C：+15.19 pp／+45.59% |

絕對差＝100×(k1−k0)，單位為百分點（pp），不是取絕對值；相對差＝100×(k1−k0)/k0，以相對百分比表示。兩者均由未四捨五入的原值計算，再顯示到小數點後兩位。

**論文比較依據**：分類使用Table 4的Small Classifier（V2）與Small Classifier + LLM（V1），未加入SRE correction。論文沒有另外列提升大小表，上欄是本次依原數值計算。Table 2的定位對照只有k1，缺少可配對的k0，因此AC@1／3／5的論文絕對與相對變化均列不可計算，不填0。

**結果解讀**：node的AC@1／3／5皆下降，pod／service皆提高；三類Micro／Macro Recall與F1提高，Precision下降。分類18個方向中16個與論文相同，兩個不同為C／Node的Micro／Macro Precision。不能描述為全面提升。

**比較限制與來源**：本次Luna替代論文GPT-4，Trace clipping及Macro F1定義差異另列，不能把差異全部歸因於LLM替換。本表取自runs/lasrca/luna_k0_k1_comparison/paper_comparison.csv；逐seed數值、checkpoint重評估與論文原始值／locator保留於同run的per_seed_comparison.csv、pairing_manifest.json及paper_comparison.md。

### 講稿備註

AC@u衡量實際故障entity是否進入模型前u名定位結果。Precision衡量預測某故障類型的結果中有多少正確，Recall衡量該故障類型中有多少被找出，F1是兩者的調和平均。Micro先合併類別計數再算指標，Macro先按類別計算再平均。公開程式的Macro F1是逐類F1平均，與論文文字及舊簡報notes所述的Macro P／R調和平均須分開。GT是評估用參考標籤，probability是類別機率，ranking是定位排序。

為了避免把資料或前處理變動誤當成補標效果，兩組除新增LLM labels外保持相同條件。各seed先配對，再彙整五組平均與母體std。百分點差為100×(k1−k0)，相對百分比為100×(k1−k0)/k0，不能混用。

本輪三類F1與Recall均提高，Precision均下降；node定位下降，pod／service定位提高。分類18個方向有16個與論文一致，兩個不同是node的Micro／Macro Precision。這支持本條件下補標效果有取捨，不能宣稱每個錯標造成某個指標變化的獨立因果證明。公開GPT-4模型的歷史evaluation與本輪Luna五seed比較屬不同實驗，不混成同一baseline。

證據：`luna_k0_k1_comparison/{pairing_manifest.json,comparison.json,per_seed_comparison.csv,summary_comparison.csv,paper_comparison.json,paper_comparison.md}`；兩個sweep的 `prediction_verification` 與各run的 `predictions`。論文表格對應及來源頁碼以 `paper_comparison` 的原文locator為準，Luna與clipping差異維持明列。

銜接：整體指標顯示升降，下一項回到實際回答，檢查哪些錯標進入了訓練。

## 0C-09 Labeling Errors Summarization｜標註錯誤與更新影響

### 介紹正文

**目標**

- 檢查LLM labels與GT不符或格式異常的情況，區分錯標與無效回答。
- 追蹤錯誤是否實際更新至dataset，說明新增監督資訊的風險。
- 以真實案例與完整回答整理錯誤類型，避免僅憑總完成率判斷標註品質。

**要求**

- 全量核對LLM labels與GT，列出10～20個不同的實際錯誤／格式異常案例。
- 每例記錄案例時間與entity、GT及來源位置、LLM label、完整response與錯誤類型。
- 關聯正式dataset diff，保存`y`／`y_mask`前後值、採用或忽略狀態及原因。
- 分開統計錯誤cases、entity occurrences及錯誤類型，交代分母與分類是否重疊。

**程式變更**

- 新增案例時間／GT定位、錯誤分類與原response對照表，再關聯正式更新結果。
- 原先模擬更新影響改以正式dataset diff核對。這些是離線重現驗證，與論文演算法無關，不用GT回填或修正LLM labels。

### 結果正文

全653 entity occurrences核對，發現86異常occurrences，分布在36個不同cases；詳細報告選20個不同cases並保存原回答及正式更新影響。

| 類型 | Entity occurrences | 正式更新影響 |
|---|---:|---|
| 漏判 | 50 | 合法但與GT不符的標籤，按規則更新 |
| 誤報 | 16 | 合法但與GT不符的標籤，按規則更新 |
| 故障類別錯判 | 7 | 合法但與GT不符的標籤，按規則更新 |
| Unknown fault | 13 | 未更新，保留原y／mask |
| 合計 | 86 | 73個合法錯標進入更新，13個unknown忽略 |

本表四類採互斥細分類，加總為86；上層label_disagrees_with_ground_truth統計包含前三類，不能再加一次。合法標籤與GT一致為567／640（88.59%）；若以全653為分母則567／653（86.83%）。兩者皆不同於06的98.01%合法率，也不同於案例層級正確率。

**真實案例**：case_index=5、2022-03-24／cloudbed-3的productcatalogservice-1。GT為K8s Disk Write IO Load，LLM摘要給No fault。正式更新y由14變0、mask由0變1，update_verified=True。這是漏判標籤實際進入監督資料的例子，沒有用GT修正。

**案例來源**：audit/error_cases.csv的case5／entity_index45；摘要原文responses/summarization/5.txt；GT來源與時間locator按CSV同列追溯。此例能證明錯標流入dataset，不能單獨證明它造成08某項指標下降。

### 講稿備註

為了判斷錯誤對訓練輸入的影響，先分兩種情況：合法故障名稱但與GT不同的錯標，會按既定更新規則成為監督訊號；unknown等無法使用的回答則保留原mask。漏判是把實際故障判為無故障，誤報是把無故障判為有故障，類別錯判是找到故障但類型不同。No fault是合法類別，unknown不是其替代寫法。

本輪653 occurrences中發現86異常entities，分布在36 cases。73個合法錯標包含50漏判、16誤報及7類別錯判，另有13 unknown。詳細報告選20個不同cases，同案例的多個entities分列，不能把20 entities當成20 cases。對原文可追查到的stage才討論形成原因，未有充分證據時標原因未確認。

本項證明哪些錯誤流入dataset，不單獨證明其對下游指標的大小或方向。進入訓練的合法錯標與未進入訓練的unknown應分開說明。

證據：`luna_20261004/audit/{errors.json,error_cases.csv,case_details.md,error_taxonomy.json,error_type_counts.csv,update_impact.jsonl,summary.json}`；GT時間／檔案locator與stage-3原回答按各案例條目定位，更新來源為 `luna_20261004/dataset/label_changes.json`。

銜接：前四項使用公開processed資料，下一項檢查從raw能否重建相應輸入。

## 0C-10 Dataset Preprocessing｜原始資料前處理重建

### 介紹正文

**目標**

- 從raw CCF AIOps 2022資料重走前處理，確認能建立分類器所需的輸入。
- 檢查各script讀寫的資料內容與數量，找出公開入口缺漏及重建差異。
- 比較自建與作者released temp_data的結構及特徵。此項是原清單的stretch goal。

**要求**

- 固定normal／train_valid／test的日期、cloudbed、原始檔與GT來源，在獨立目錄保存重建結果。
- 完成topology、entity edge index、time windows／labels，以及Metric／Trace／Log擷取與轉換，最後組裝dataset，共10個scripts。
- 各script保存輸入／輸出內容數量、計數單位、schema、duration、exit status及失敗／中斷證據，建立final manifest。
- 抽樣對照shape、timestamps、三模態feature名稱／數值；另核對覆蓋範圍內labels與topology，明列差異及比較範圍。

**程式變更**

- 補齊test GT JSON至CSV的無損格式轉換，啟用原入口漏跑的Istio擷取及四類Metric標準化，處理重跑目錄已存在的情況。
- 修正全NaN／零變異Metric分支沿用前一特徵值的問題，明確產生零值。此為數值行為差異，須記錄對released比較的影響。
- 新增逐script數量與產物歸屬核對，分開觀測列、feature cells、時間窗、label values與edges。上述補齊、修正與紀錄不列為論文提出的演算法。

### 結果正文

抽樣及全量各10 scripts全部exit0；全量manifest有5191 artifacts（含4份configuration inputs）、抽樣717，unknown producer=0，inspection failures=[]。

| Script | 唯一輸入檔 | 輸出檔 | Duration秒 | Exit |
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

檔案數不能代替內容數量。完整逐script／field數量、單位及schema保留在stage_count_summary.csv與stage_input_output_counts.csv；以下列主要內容結果。

| 檢查對象 | 結果 | 範圍／解讀 |
|---|---|---|
| Window size9 labels | 4714 windows，4714 label vectors，263984 entity label values；GT無差 | 覆蓋範圍全量核對；不同window sizes分列 |
| Topology | 15組covered edge sets無差；15份輸出共2460 stored directed edges | 不含公開入口額外生成的30份out-of-scope topology entries |
| Final observations | Processed 1,209,600 entity-minute rows、44,582,400 feature cells；raw欄位另同量保存 | rows／cells分開，raw與processed不相加當案例數 |
| Final metadata edges | 7380 stored directed edges | 儲存結構含重複引用，不等於7380唯一邊 |
| 抽樣shape／timestamps | 9份DataFrame皆1440 timestamps對齊；node1440×25、pod1440×47、service1440×9 | normal／train_valid／test各第一date/cloud、各類第一entity |
| Metric／Trace／Log數值 | 234 feature比較列中228在1e-6容許內、6不同 | node72／service24皆符合；pod138中6項Istio不同，最大差約19.617 |
| Log coverage | 全量fit後9個Log features齊全 | 抽樣fit缺欄已補；名稱相同但C#與Java／Python欄位順序不同 |

**結果解讀**：流程完成與結構對齊成立，並非全量所有特徵逐值一致。6個差異是三split的Istio request_messages.source／response_messages.source；Log欄位應依名稱對齊後才能混用矩陣。全NaN／零變異分支的修正會改變部分Metric數值，已獨立揭露。

**Log的實際用途**：Log DAO解析事件templates，generator產生時間特徵並組入pod資料。此處重新生成Log特徵；07／08使用的是作者released processed資料的Log特徵，不把raw重建結果混入主比較。

**保存與限制**：舊計數表保留在accounting_before_correction_20261005。計數依程式讀寫位置與保留schema重建，非歷史逐次I/O tracing。歷史中斷留snapshot／logs；全量沒有獨立failures.jsonl，不能將缺檔描述為已保存。作者可能手動改前處理入口仍是推測。

### 講稿備註

raw是本次讀入的公開原始觀測來源，released temp_data是作者已完成前處理的產物。Metric是時間序列量測，Trace記錄服務呼叫，Log是事件文字；schema描述欄位／結構，shape描述矩陣尺寸，manifest列產物路徑與版本識別。cloudbed是資料內的部署環境分組。stretch goal表示超出前段僅載入作者產物的重現深度。

為了確認分類器輸入如何產生，先固定原始資料範圍並建立entities、關係與故障時間窗，再從三模態生成可用特徵，最後組裝dataset。不同script使用不同資料單位，不能都稱「筆數」或把檔案數當觀測數。計數依公開程式讀寫位置與保存schema重建，表示唯一依賴檔案／內容數量，沒有歷史逐次I/O tracing。node／service的首CSV選擇依現存資料夾順序推定，限制須明列。

抽樣與全量各10 scripts皆exit0、unknown producer=0。全量覆蓋4714時間窗及15組拓樸，labels／edge sets無差。抽查9份DataFrame的shape及1440 timestamps對齊，234 feature比較列中6個pod Istio數值有差；9個Log features全量fit後齊全，但欄位順序仍須對齊。fit是由資料估計統計量或template，抽樣與全量fit的範圍不同，不能用抽樣缺欄直接判定全流程失敗。

來源程式是否曾由作者手動修改入口仍是推測。補齊CSV及入口後能跑完，不等於已還原作者執行歷史。此次raw重建資料也沒有用於前面Luna主比較或TS2Vec兩輪自訓，不能將其數值差異直接歸因為那些模型的效果變化。

證據：`raw_full_20261004/{config.json,stage_script_summary.json,stage_count_summary.csv,stage_input_output_counts.csv,stage_schemas.json,stage_runs.jsonl,pipeline_status.json,evidence_failures.json,final_manifest.json}`、各script logs及 `comparison/{shapes.csv,feature_summary.csv,labels.json,topology.json}`；抽樣在 `raw_20261004`。全量沒有獨立failures.jsonl，歷史中斷保留在snapshot及logs。十script名單與執行順序見 `code/experiments/raw_pipeline.py`。

銜接：下一項獨立採作者公開processed資料，檢查自行訓練encoder後的向量與下游結果。

## 0C-11 TS2Vec embedding Training｜觀測encoder自訓與對照

### 介紹正文

**目標**

- 至少自行訓練一組TS2Vec觀測encoder，檢查觀測序列能否轉為下游使用的embedding。
- 比較自訓embedding與作者公開embedding，以及替換後的RCA指標差異。
- 明確區分作者提供的向量、自訓模型與下游分類器。此項是原清單的stretch goal。

**要求**

- 以作者公開processed資料訓練service encoder，固定8個Metric輸入及特徵順序；node／pod沿用作者embedding。
- 依公開service設定訓練600 epochs，保存dataset／SHA-256、seed、batch32、lr0.001、320維輸出、最大訓練長度3000，以及完整defaults。
- 保存loss curve、duration與encoder checkpoint，對全150段service序列檢查coverage、shape及NaN／Inf。
- 替換service embedding，以相同下游split／labels／seed405各訓練500 epochs，比較embedding與classification／localization指標。
- 保存原seed405結果，追加encoder seed406對照；下游seed保持405，記錄兩次自訓與公開基準的差異。

**程式變更**

- 新增作者archive／processed input來源與實際設定核對、訓練紀錄、全序列encoding及逐序列比較。
- 兩組下游使用獨立cache，核對實際讀入的embedding，避免舊資料快取使替換未生效。
- 新增下游定位評估與三版本對照，補足原路線的比較證據。以上保存、隔離及評估功能與論文演算法無關；追加seed406屬使用者要求的額外對照。

### 結果正文

作者公開包包含embedding_600.pkl及下游模型，沒有TS2Vec encoder權重。自訓seed405、406皆使用同一作者released processed資料（SHA-256與archive entry一致），service只含8個Metric；node／pod沿用作者embedding。

| 執行檢查 | 結果 |
|---|---|
| Encoder訓練 | 405／406各600 epochs，checkpoint、完整loss與設定已保存 |
| 全序列encoding | 兩輪皆150 service序列，1440×320，coverage／finite檢查通過 |
| 下游比較 | 公開／自訓兩路各500 epochs，固定下游seed405、split／labels一致 |
| 公開基準重跑 | 36項指標與上一輪完全一致 |
| Seed405耗時 | 訓練含載入及單序列檢查總3161.953秒，全150序列encoding 3225.640秒 |
| Timing界線 | 純訓練／單序列encoding歷史未獨立量測，保存null |

以下為下游seed405的百分比指標；405／406是encoder seed。此表不是五seed平均，故不報mean±std。最後兩欄為各自訓版本相對公開embedding的百分點差。

#### node

| Metric | 公開embedding (%) | Encoder405 (%) | Encoder406 (%) | 405差pp | 406差pp |
|---|---:|---:|---:|---:|---:|
| AC@1 | 35.8209 | 32.8358 | 37.3134 | -2.9851 | +1.4925 |
| AC@3 | 67.1642 | 62.6866 | 64.1791 | -4.4776 | -2.9851 |
| AC@5 | 79.1045 | 70.1493 | 76.1194 | -8.9552 | -2.9851 |
| Micro P | 0.9131 | 0.9156 | 0.9048 | +0.0025 | -0.0083 |
| Micro R | 68.6567 | 68.6567 | 68.6567 | 0.0000 | 0.0000 |
| Micro F1 | 1.8022 | 1.8071 | 1.7861 | +0.0049 | -0.0161 |
| Macro P | 1.1676 | 1.1681 | 1.1689 | +0.0005 | +0.0013 |
| Macro R | 70.4606 | 70.4606 | 70.4606 | 0.0000 | 0.0000 |
| Macro F1 | 2.2633 | 2.2643 | 2.2642 | +0.0010 | +0.0009 |

#### pod

| Metric | 公開embedding (%) | Encoder405 (%) | Encoder406 (%) | 405差pp | 406差pp |
|---|---:|---:|---:|---:|---:|
| AC@1 | 29.0698 | 27.9070 | 30.2326 | -1.1628 | +1.1628 |
| AC@3 | 50.0000 | 46.5116 | 47.6744 | -3.4884 | -2.3256 |
| AC@5 | 60.4651 | 55.8140 | 54.6512 | -4.6512 | -5.8140 |
| Micro P | 0.7808 | 0.7769 | 0.7856 | -0.0039 | +0.0048 |
| Micro R | 38.1279 | 37.8995 | 38.3562 | -0.2284 | +0.2283 |
| Micro F1 | 1.5302 | 1.5225 | 1.5397 | -0.0077 | +0.0095 |
| Macro P | 2.8210 | 2.8250 | 2.8325 | +0.0040 | +0.0115 |
| Macro R | 37.3703 | 37.1524 | 37.5337 | -0.2179 | +0.1634 |
| Macro F1 | 4.9541 | 4.9589 | 4.9769 | +0.0048 | +0.0228 |

#### service

| Metric | 公開embedding (%) | Encoder405 (%) | Encoder406 (%) | 405差pp | 406差pp |
|---|---:|---:|---:|---:|---:|
| AC@1 | 34.0909 | 35.2273 | 34.0909 | +1.1364 | 0.0000 |
| AC@3 | 56.8182 | 55.6818 | 55.6818 | -1.1364 | -1.1364 |
| AC@5 | 68.1818 | 72.7273 | 70.4545 | +4.5455 | +2.2727 |
| Micro P | 0.5772 | 0.5800 | 0.5731 | +0.0028 | -0.0041 |
| Micro R | 31.8182 | 34.0909 | 30.6818 | +2.2727 | -1.1364 |
| Micro F1 | 1.1338 | 1.1407 | 1.1252 | +0.0069 | -0.0086 |
| Macro P | 0.8697 | 0.8426 | 0.9070 | -0.0271 | +0.0373 |
| Macro R | 33.2099 | 36.2346 | 33.2099 | +3.0247 | 0.0000 |
| Macro F1 | 1.6335 | 1.6073 | 1.6930 | -0.0262 | +0.0595 |

**結果解讀**：兩個自訓encoder的service AC@5皆提高，node／pod AC@5皆下降；AC@1與分類指標的方向會隨encoder seed改變。service Macro F1只有約1.6～1.7%，微小差異不能描述為良好分類能力。只替換service向量仍會影響其他entities的下游結果。

**因果界線**：固定公開資料與下游條件、公開基準重跑一致，支持差異與重新學得的embedding及下游互動有關。兩次都未使用新raw資料，所以不能將這兩輪效果差異歸因於新raw；也不能因此證明新raw沒有問題。兩個encoder seeds／單一下游seed不支持穩定性或統計顯著性結論。

**Embedding數值比較**：以下由各encoding_manifest的150個序列差異彙整，每個序列等權。MAE指對齊位置的平均絕對差，數值沒有accuracy單位，也不表示品質優劣。

| Encoder seed | 序列數 | 序列MAE平均 | 最小／最大序列MAE | 全部位置最大絕對差 | 全量encoding秒 |
|---|---:|---:|---:|---:|---:|
| 405 | 150 | 0.223489 | 0.201143／2.055089 | 47.510788 | 3225.640 |
| 406 | 150 | 0.231620 | 0.207767／1.985122 | 46.720703 | 3052.812 |

**Embedding差異來源**：逐序列shape／MAE等數值保存在第一輪encoding_manifest.json與追加encoding產物，完整下游36指標見三版本CSV。Embedding數值差異不直接等於模型品質。

### 講稿備註

TS2Vec是將觀測時間序列轉成向量的encoder。checkpoint保存模型參數，embedding保存模型算出的向量，兩者不能互稱。作者下載包的 `model.zip` 提供下游模型，沒有TS2Vec權重；`embedding_600.pkl` 是作者已算好的embedding。因此公開基準使用作者向量，自訓路線訓練我們的encoder再產生向量。下游程式直接讀入固定embedding，沒有在此次下游訓練中端到端更新TS2Vec。

本輪只自訓service的8個Metric，沒有把Trace／Log加入service輸入。先固定資料與特徵順序，使用作者公開設定訓練600 epochs，再以相同encoding設定生成150段序列的1440×320向量。coverage表示預期序列皆有輸出，NaN／Inf是非有限值；loss顯示訓練目標的變化，不能直接當RCA accuracy。batch、lr與最大訓練長度分別指每次訓練的序列數、參數更新步幅及訓練序列長度上限。

為了比較下游效果，只替換service embedding，保持node／pod作者向量、split、labels與下游seed相同。隔離cache讓程式讀入正確版本。service向量可經圖模型與下游重訓影響node／pod結果，所以「只替換service」不代表只有service指標會變。

seed405及追加406的encoder都使用同一作者公開processed input，其SHA與archive entry一致，均未使用本次raw重建資料。公開基準在同下游seed重跑的36指標一致；兩個自訓encoder的下游結果仍有升有降。這支持encoder隨機性與重新學得的embedding影響結果，不能推定新raw資料導致下降，也不能因此證明新raw沒有問題。作者encoder seed未知，兩個encoder seeds加單一下游seed不足以宣稱穩定性或精確還原作者模型。

證據：`ts2vec_20261004/{input_manifest.json,loss.csv,loss_curve.png,timing.json,model.pkl}`、`ts2vec_downstream/{encoding_manifest.json,service_replaced.pkl}`、`encoder_pair_20261004/comparison.json`；追加run `encoder_public_recheck_20261005/{protocol.json,public_input_provenance.json,status.json}` 、`downstream/comparison.json`、run根目錄的 `three_variant_comparison.csv` 與 `verification_and_three_variants.json`。公開設定來源為 `code/pretrain.sh` 與 `code/pretrain/train.py`，下載包與實際輸入的核對見 [encoder來源報告](encoder_public_provenance.md)。未獨立量測的歷史耗時保持null，不把載入／樣本encoding總耗時全稱純訓練時間。

銜接至結論：六項完成代表既定流程與保存／比較要求完成。Luna替代設定、錯標、raw特徵差異及encoder對照範圍，仍是解讀實驗結果時必須保留的界線。

## 後續製作結果頁時的素材

本版已加入六項結果。完整逐seed／逐案例資料可從 [六項結案報告](six_tasks_closure_20261005.md)、[第一輪結果](one_round_results_20261004.md) 與 [encoder來源／追加結果](encoder_public_provenance.md) 取用數值與來源。LLM標註率、五seed重訓表、k0／k1比較、真實錯誤案例、raw對照與encoder三版本比較應分開呈現，避免用一張「全部完成」表取代必要的結果及限制。
