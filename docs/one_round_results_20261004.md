# LasRCA 後六項：第一輪實驗結果與验收界線

2026-10-04 23:14核對；最後一條流程於22:37完成。這表示六項都實際走過一輪，可以開始人工驗收，不表示完全重現論文數值或所有差異原因均已解決。原始reproduction_staus_original.md未修改，SHA256仍為9F6251D901534C47E8CC2059DB8B1E27BFAC8F9CD98775F88AF775AA73E0B0F0。

## 六項完成證據

| 任務 | 實際完成 | 證據位置（相對runs/lasrca） |
|---|---|---|
| 06 Luna四階段標註 | 100／100cases，100摘要可解析；653個entity occurrences，640合法labels、13個unknown_fault | `luna_20261004/{status.json,labeling_report.json,labels,responses,usage,errors}` |
| 07 更新與重訓 | 新增640個mask0→1；13個unknown保留原y／mask；正式dataset，完整前後快照／分布，features、split、protected labels不變；seeds405～409各500epochs | `luna_20261004/dataset`、`luna_k1_no_std/sweep_status.json`及五個run |
| 08 成對比較 | k0與k1五seed；checkpoint hash核對，重評估12指標一致；成對輸入條件、逐seed、mean±母體std、絕對／相對差、論文方向表完成 | `luna_k0_k1_comparison`、兩個sweep的`prediction_verification` |
| 09 錯誤分析 | 全653entity核對；86個錯誤／格式異常entities、36個不同cases；列20個不同案例的完整stage3回答與正式更新影響 | `luna_20261004/audit/{errors.json,error_cases.csv,case_details.md,error_taxonomy.json,error_type_counts.csv,update_impact.jsonl,summary.json}` |
| 10 原始資料全量前處理 | 抽樣及全量10stage全部exit0；全量5187artifacts掃描，0inspection failures；4714時間窗GT與15拓樸均0差異；schemas／counts／timings／failure history／manifest及特徵比較已保存 | `raw_full_20261004`及`comparison`；抽樣另在`raw_20261004` |
| 11 自訓TS2Vec與下游 | service／8個Metric、seed405、600epochs；150序列encoding全部完成；released／self-service兩組下游各500epochs，同split／labels，分類與定位比較完成 | `ts2vec_20261004`、`ts2vec_downstream`、`encoder_pair_20261004` |

原controller的classifiers failed是20:52資料更新失敗的歷史；修正後最新classifiers狀態在`round_followup_recovery_20261004/status.json`，已completed。原controller的preprocessing與encoder亦completed。不能因舊failed欄位將此次成功誤判為仍中斷，也不覆寫失敗歷史。

## 補標後的主要結果

五seed mean，比例轉百分比；括號為k1−k0百分點。完整mean±std與36指標見比較表，不能用下表取代逐seed證據。

| Entity | AC@1 k0→k1 | AC@3 k0→k1 | AC@5 k0→k1 | Micro F1 k0→k1 | Macro F1 k0→k1 |
|---|---|---|---|---|---|
| node | 79.40→76.42（−2.99） | 89.55→88.06（−1.49） | 92.54→90.45（−2.09） | 36.70→44.51（+7.80） | 36.01→41.05（+5.04） |
| pod | 56.28→58.37（+2.09） | 67.21→70.23（+3.02） | 71.16→76.51（+5.35） | 41.36→57.09（+15.73） | 40.14→56.22（+16.08） |
| service | 78.86→79.55（+0.68） | 86.82→89.77（+2.95） | 92.27→92.50（+0.23） | 39.00→54.49（+15.48） | 36.19→51.76（+15.57） |

三類F1與Recall均提高，Precision均下降；node定位下降，pod／service定位提高。分類的18個方向中16個與原Table4相同，兩個不同的是node Micro／Macro Precision。因此補標帶來較多故障預測，同時也增加誤報；不能描述為全面提升。這是同條件成對實驗的可觀察結果，不是對每個錯標如何影響最終模型的獨立因果證明。論文值與定義界線另見`paper_comparison.md`；Luna及stored percentile clipping不同於原GPT-4條件，MacroF1沿用公開程式逐類F1平均，不能聲稱精確重現論文公式。

錯標細分：73個合法label與GT不同，其中漏判50、誤報16、故障類別錯判7；另有13個unknown。前者會成為合法但與GT不符的監督訊號，後者被忽略。GT只用於離線驗收，不拿GT修正Luna輸出。86不是全部無效格式，不能把合法錯標與unknown混為一談；也不能用640／653的格式有效率當正確率。

成功unique requests共2479，returned model均gpt-6-luna；input tokens 3,801,843、output 737,533、total 4,539,376。此統計只涵蓋有metadata的成功请求，快取重用不重複計算；失敗請求的用量不可推定。保存的USD0.6681是公開API牌價等值估算，OAuth實際扣額／費用不可得，不是帳單。

## Raw數值與特徵差異

全量fit後，抽樣曾缺少的9個Log features全部產生；這支持其差異與抽樣fit範圍相關，但並不證明每一步的作者執行歷史。全量抽查normal／train_valid／test各第一個date/cloud及每entity type第一個entity：9份DataFrame都對齊1440timestamps，node1440×25、service1440×9、pod1440×47，與released shape相同。

依名稱比較234個feature rows：node72、service24均在1e-6容許值內；pod138中6個數值不同，均為三個split的Istio request_messages.source／response_messages.source。最大差約19.617。已保存逐feature mean／max差及前五timestamps，精確原因仍待核對。pod Log九欄名稱集合相同，但C#與Java／Python欄位順序不同；使用矩陣位置的下游不能直接混用，必須依feature name對齊。

這是指定抽樣的數值比較，不是全量所有entity/feature逐值一致驗證。已確認全NaN／零std Metric分支改為明確零值，相對released沿用上一特徵是數值修正差異；抽查adservice不代表cartservice等所有entity也相同。全量GT／topology則是所有覆蓋範圍核對，4714windows與15edge sets皆相同；公開入口額外產生30份不在config範圍的拓樸，已明列排除，不冒充coverage。

## Encoder結果及邊界

**2026-10-05來源更正：** 作者下載包提供`embedding_600.pkl`及下游模型，沒有TS2Vec encoder權重。此處released指作者已算好的embedding，不是作者TS2Vec模型。上一輪自訓使用作者released processed dataset，而非本次raw重建資料；因此其效果差異不能歸因於新raw資料。下載包核對、實際輸入hash與追加公開資料seed406對照見[來源說明](encoder_public_provenance.md)。

僅自訓service encoder，node／pod沿用released。下游seed405：service AC@1提升1.14pp、AC@5提升4.55pp，MacroF1下降0.03pp；node／pod AC@1下降2.99／1.16pp。只替換service仍可透過圖模型及重訓影響其他entity輸出。只跑一seed，不能宣稱五seed穩定性，也不能把embedding MAE當模型品質。

原FineTuning入口的source split行為保持原樣，不能聲稱額外建立獨立驗證集。TS2Vec training加單序列檢查總耗時3161.953秒，不冒稱純訓練時間；全150序列encoding耗時3225.64秒。歷史未單獨量測的項目在timing.json明列null。

## 待人工驗收及尚未證實事項

1. 核對上述五seed比較與paper_comparison，接受結果有升有降；不宣稱統計顯著性或完全重現GPT-4結果。
2. 檢查20個真實錯誤案例及正式y／mask影響，尤其50個漏判與13個unknown；不自動用GT修正。
3. 追查全量pod的六個Istio數值差異與Log欄位順序。檔案已保存，這不是執行中斷，也未擅自改成released答案。
4. 如需所有entity／日期逐值比較或多seed encoder評估，屬超出本輪既定驗證範圍的後續工作，須另定範圍。
5. OAuth實際扣額、作者是否手動改腳本分批處理、論文MacroF1實際計算方式仍不可由現有證據確定。

OAuth／DPAPI、成功快取、checkpoint恢復、controller、CSV／hash／manifest、counts／schemas、輸入保護、測試及新增FineTuning定位輸出均為與論文演算法無關的執行支援或重現驗證。Luna、额外clipping、raw數值修正與encoder部分替換則是實驗條件差異，不能只標為記錄工具。
