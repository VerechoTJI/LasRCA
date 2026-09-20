temp_data/
├─ 2022_CCF_AIOps_challenge/
│  ├─ .DS_Store
│  ├─ analysis/
│  │  ├─ log/
│  │  │  ├─ container_log_selected_patterns.json
│  │  │  ├─ container_log_statistic.json
│  │  │  ├─ container_log_tf_idf_statistic.json
temp_data/
├─ 2022_CCF_AIOps_challenge/
│  ├─ .DS_Store
│  ├─ analysis/
│  │  ├─ log/
│  │  │  ├─ container_log_selected_patterns.json
│  │  │  ├─ container_log_statistic.json
│  │  │  ├─ container_log_tf_idf_statistic.json
│  │  │  ├─ istio_log_statistic.json
│  │  │  ├─ istio_log_tf_idf_statistic.json
│  │  │  ├─ istio_selected_words.json
│  │  │  ├─ istio_words.json
│  │  │  ├─ log_patterns.json
│  │  │  └─ log_template_miner.pkl
│  │  ├─ metric/
│  │  │  └─ common_statistic.json
│  │  └─ trace/
│  │     ├─ statistic.json
│  │     └─ trace_patterns.json
│  ├─ dataset/
│  │  ├─ ent_edge_index/
│  │  │  └─ ent_edge_index.pkl
│  │  ├─ final/
│  │  │  └─ metric_trace_log.pkl
│  │  ├─ log/
│  │  │  ├─ all_log.pkl
│  │  │  ├─ log_window_size_9.pkl
│  │  │  ├─ z_scored_container_log_features.pkl
│  │  │  └─ z_scored_istio_features.pkl
│  │  ├─ metric/
│  │  │  └─ all_metric.pkl
│  │  ├─ time_interval_and_label/
│  │  │  └─ time_interval_window_size_9.pkl
│  │  └─ trace/
│  │     ├─ all_trace.pkl
│  │     └─ all_trace_features.pkl
│  └─ raw_data/
│     ├─ normal/
│     │  └─ 2022-03-19/
│     │     ├─ cloudbed-1/
│     │     │  ├─ raw_log/
│     │     │  │  ├─ istio_word_count.csv
│     │     │  │  └─ log_patterns_count.csv
│     │     │  ├─ raw_metric/
│     │     │  │  ├─ container/
│     │     │  │  │  ├─ adservice-0.csv
│     │     │  │  │  ├─ adservice-1.csv
│     │     │  │  │  ├─ adservice-2.csv
│     │     │  │  │  ├─ adservice2-0.csv
│     │     │  │  │  ├─ cartservice-0.csv
│     │     │  │  │  ├─ cartservice-1.csv
│     │     │  │  │  ├─ cartservice-2.csv
│     │     │  │  │  ├─ cartservice2-0.csv
│     │     │  │  │  ├─ checkoutservice-0.csv
│     │     │  │  │  ├─ checkoutservice-1.csv
│     │     │  │  │  ├─ checkoutservice-2.csv
│     │     │  │  │  ├─ checkoutservice2-0.csv
│     │     │  │  │  ├─ currencyservice-0.csv
│     │     │  │  │  ├─ currencyservice-1.csv
│     │     │  │  │  ├─ currencyservice-2.csv
│     │     │  │  │  ├─ currencyservice2-0.csv
│     │     │  │  │  ├─ emailservice-0.csv
│     │     │  │  │  ├─ emailservice-1.csv
│     │     │  │  │  ├─ emailservice-2.csv
│     │     │  │  │  ├─ emailservice2-0.csv
│     │     │  │  │  ├─ frontend-0.csv
│     │     │  │  │  ├─ frontend-1.csv
│     │     │  │  │  ├─ frontend-2.csv
│     │     │  │  │  ├─ frontend2-0.csv
│     │     │  │  │  ├─ paymentservice-0.csv
│     │     │  │  │  ├─ paymentservice-1.csv
│     │     │  │  │  ├─ paymentservice-2.csv
│     │     │  │  │  ├─ paymentservice2-0.csv
│     │     │  │  │  ├─ productcatalogservice-0.csv
│  │  │  │  │  ├─ productcatalogservice-1.csv
│  │  │  │  │  ├─ productcatalogservice-2.csv
│  │  │  │  │  ├─ productcatalogservice2-0.csv
│  │  │  │  │  ├─ recommendationservice-0.csv
│  │  │  │  │  ├─ recommendationservice-1.csv
│  │  │  │  │  ├─ recommendationservice-2.csv
│  │  │  │  │  ├─ recommendationservice2-0.csv
│  │  │  │  │  ├─ shippingservice-0.csv
│  │  │  │  │  ├─ shippingservice-1.csv
│  │  │  │  │  ├─ shippingservice-2.csv
│  │  │  │  │  └─ shippingservice2-0.csv
│  │  │  │  ├─ istio/
│  │  │  │  │  ├─ adservice-0.csv
│  │  │  │  │  ├─ adservice-1.csv
│  │  │  │  │  ├─ adservice-2.csv
│  │  │  │  │  ├─ adservice2-0.csv
│  │  │  │  │  ├─ cartservice-0.csv
│  │  │  │  │  ├─ cartservice-1.csv
│  │  │  │  │  ├─ cartservice-2.csv
│  │  │  │  │  ├─ cartservice2-0.csv
│  │  │  │  │  ├─ checkoutservice-0.csv
│  │  │  │  │  ├─ checkoutservice-1.csv
│  │  │  │  │  ├─ checkoutservice-2.csv
│  │  │  │  │  ├─ checkoutservice2-0.csv
│  │  │  │  │  ├─ currencyservice-0.csv
│  │  │  │  │  ├─ currencyservice-1.csv
│  │  │  │  │  ├─ currencyservice-2.csv
│  │  │  │  │  ├─ currencyservice2-0.csv
│  │  │  │  │  ├─ emailservice-0.csv
│  │  │  │  │  ├─ emailservice-1.csv
│  │  │  │  │  ├─ emailservice-2.csv
│  │  │  │  │  ├─ emailservice2-0.csv
│  │  │  │  │  ├─ frontend-0.csv
│  │  │  │  │  ├─ frontend-1.csv
│  │  │  │  │  ├─ frontend-2.csv
│  │  │  │  │  ├─ frontend2-0.csv
│  │  │  │  │  ├─ paymentservice-0.csv
│  │  │  │  │  ├─ paymentservice-1.csv
│  │  │  │  │  ├─ paymentservice-2.csv
│  │  │  │  │  ├─ paymentservice2-0.csv
│  │  │  │  │  ├─ productcatalogservice-0.csv
│  │  │  │  │  ├─ productcatalogservice-1.csv
│  │  │  │  │  ├─ productcatalogservice-2.csv
│  │  │  │  │  ├─ productcatalogservice2-0.csv
│  │  │  │  │  ├─ recommendationservice-0.csv
│  │  │  │  │  ├─ recommendationservice-1.csv
│  │  │  │  │  ├─ recommendationservice-2.csv
│  │  │  │  │  ├─ recommendationservice2-0.csv
│  │  │  │  │  ├─ shippingservice-0.csv
│  │  │  │  │  ├─ shippingservice-1.csv
│  │  │  │  │  ├─ shippingservice-2.csv
│  │  │  │  │  └─ shippingservice2-0.csv
│  │  │  │  ├─ node/
│  │  │  │  │  ├─ node-1.csv
│  │  │  │  │  ├─ node-2.csv
│  │  │  │  │  ├─ node-3.csv
│  │  │  │  │  ├─ node-4.csv
│  │  │  │  │  ├─ node-5.csv
│  │  │  │  │  └─ node-6.csv
│  │  │  │  └─ service/
│  │  │  │     ├─ adservice.csv
│  │  │  │     ├─ cartservice.csv
│  │  │  │     ├─ checkoutservice.csv
│  │  │  │     ├─ currencyservice.csv
│  │  │  │     ├─ emailservice.csv
│  │  │  │     ├─ frontend.csv
│  │  │  │     ├─ paymentservice.csv
│  │  │  │     ├─ productcatalogservice.csv
│  │  │  │     ├─ recommendationservice.csv
│  │  │  │     └─ shippingservice.csv
│  │  │  └─ raw_trace/
│  │  │     └─ span_features.csv
│  │  ├─ cloudbed-2/
│  │  │  ├─ raw_log/
│  │  │  │  ├─ istio_word_count.csv
│  │  │  │  └─ log_patterns_count.csv
│  │  │  ├─ raw_metric/
│  │  │  │  ├─ container/
│  │  │  │  ├─ istio/
│  │  │  │  ├─ node/
│  │  │  │  └─ service/
│  │  │  ├─ raw_trace/
│  │  │  │  └─ span_features.csv
│  │  │  └─ resource_entity/
│  │  │     └─ edge_index.pkl
│  │  └─ cloudbed-3/
│  │     ├─ raw_log/
│  │     │  ├─ istio_word_count.csv
│  │     │  └─ log_patterns_count.csv
│  │     ├─ raw_metric/
│  │     │  ├─ container/
│  │     │  ├─ istio/
│  │     │  ├─ node/
│  │     │  └─ service/
│  │     ├─ raw_trace/
│  │     │  └─ span_features.csv
│  │     └─ resource_entity/
│  │        └─ edge_index.pkl
│  ├─ test/
│  │  ├─ 2022-05-01/
│  │  │  └─ cloudbed/
│  │  │     ├─ raw_log/
│  │  │     ├─ raw_metric/
│  │  │     ├─ raw_trace/
│  │  │     └─ resource_entity/
│  │  ├─ 2022-05-03/
│  │  │  └─ cloudbed/
│  │  │     ├─ raw_log/
│  │  │     ├─ raw_metric/
│  │  │     ├─ raw_trace/
│  │  │     └─ resource_entity/
│  │  ├─ 2022-05-05/
│  │  │  └─ cloudbed/
│  │  │     ├─ raw_log/
│  │  │     ├─ raw_metric/
│  │  │     ├─ raw_trace/
│  │  │     └─ resource_entity/
│  │  ├─ 2022-05-07/
│  │  │  └─ cloudbed/
│  │  │     ├─ raw_log/
│  │  │     ├─ raw_metric/
│  │  │     ├─ raw_trace/
│  │  │     └─ resource_entity/
│  │  └─ 2022-05-09/
│  │     └─ cloudbed/
│  │        ├─ raw_log/
│  │        ├─ raw_metric/
│  │        ├─ raw_trace/
│  │        └─ resource_entity/
│  └─ train_valid/
│     ├─ 2022-03-20/
│     │  ├─ cloudbed-1/
│     │  │  ├─ raw_log/
│     │  │  ├─ raw_metric/
│     │  │  ├─ raw_trace/
│     │  │  └─ resource_entity/
│     │  ├─ cloudbed-2/
│     │  │  ├─ raw_log/
│     │  │  ├─ raw_metric/
│     │  │  ├─ raw_trace/
│     │  │  └─ resource_entity/
│     │  └─ cloudbed-3/
│     │     ├─ raw_log/
│     │     ├─ raw_metric/
│     │     ├─ raw_trace/
│     │     └─ resource_entity/
│     ├─ 2022-03-21/
│     │  ├─ cloudbed-1/
│     │  │  ├─ raw_log/
│     │  │  ├─ raw_metric/
│     │  │  ├─ raw_trace/
│     │  │  └─ resource_entity/
│     │  ├─ cloudbed-2/
│     │  │  ├─ raw_log/
│     │  │  ├─ raw_metric/
│     │  │  ├─ raw_trace/
│     │  │  └─ resource_entity/
│     │  └─ cloudbed-3/
│     │     ├─ raw_log/
│     │     ├─ raw_metric/
│     │     ├─ raw_trace/
│     │     └─ resource_entity/
│     └─ 2022-03-24/
│        └─ cloudbed-3/
│           ├─ raw_log/
│           ├─ raw_metric/
│           ├─ raw_trace/
│           └─ resource_entity/
└─ A/
	├─ embeddings/
	│  └─ embedding_600.pkl
	├─ example_selection/
	│  └─ example_1.json
	├─ llm/
	│  ├─ .DS_Store
	│  ├─ prompts/
	│  │  ├─ .DS_Store
	│  │  └─ iteration-0/
	│  │     ├─ .DS_Store
	│  │     ├─ explanation/
	│  │     │  ├─ 0/
	│  │     │  ├─ 1/
	│  │     │  ├─ 10/
	│  │     │  ├─ 100/
	│  │     │  ├─ 101/
	│  │     │  ├─ 102/
	│  │     │  ├─ 103/
	│  │     │  ├─ 104/
	│  │     │  ├─ 105/
	│  │     │  ├─ 106/
	│  │     │  ├─ 107/
	│  │     │  ├─ 108/
	│  │     │  ├─ 109/
	│  │     │  ├─ 111/
	│  │     │  ├─ 112/
	│  │     │  ├─ 113/
	│  │     │  ├─ 114/
	│  │     │  ├─ 115/
	│  │     │  ├─ 117/
	│  │     │  ├─ 118/
	│  │     │  ├─ 119/
	│  │     │  ├─ 12/
	│  │     │  ├─ 120/
	│  │     │  ├─ 121/
	│  │     │  ├─ 123/
	│  │     │  ├─ 125/
	│  │     │  ├─ 126/
	│  │     │  ├─ 127/
	│  │     │  ├─ 128/
	│  │     │  ├─ 129/
	│  │     │  ├─ 13/
	│  │     │  ├─ 130/
	│  │     │  ├─ 131/
	│  │     │  ├─ 132/
	│  │     │  ├─ 133/
	│  │     │  ├─ 134/
	│  │     │  ├─ 135/
	│  │     │  ├─ 136/
	│  │     │  ├─ 138/
	│  │     │  ├─ 139/
	│  │     │  ├─ 14/
	│  │     │  ├─ 140/
	│  │     │  ├─ 141/
	│  │     │  ├─ 142/
	│  │     │  ├─ 143/
	│  │     │  ├─ 144/
	│  │     │  ├─ 145/
	│  │     │  ├─ 147/
	│  │     │  ├─ 148/
	│  │     │  ├─ 15/
	│  │     │  ├─ 150/
	│  │     │  ├─ 151/
	│  │     │  ├─ 152/
	│  │     │  ├─ 153/
	│  │     │  ├─ 154/
	│  │     │  ├─ 155/
	│  │     │  ├─ 157/
	│  │     │  ├─ 158/
	│  │     │  ├─ 159/
	│  │     │  ├─ 16/
	│  │     │  ├─ 161/
	│  │     │  ├─ 162/
	│  │     │  ├─ 163/
	│  │     │  ├─ 164/
	│  │     │  ├─ 167/
	│  │     │  ├─ 168/
	│  │     │  ├─ 169/
	│  │     │  ├─ 17/
	│  │     │  ├─ 171/
	│  │     │  ├─ 172/
	│  │     │  ├─ 174/
	│  │     │  ├─ 175/
	│  │     │  ├─ 176/
	│  │     │  ├─ 177/
	│  │     │  ├─ 178/
	│  │     │  ├─ 179/
	│  │     │  ├─ 18/
	│  │     │  ├─ 180/
	│  │     │  ├─ 181/
	│  │     │  ├─ 182/
	│  │     │  ├─ 183/
	│  │     │  ├─ 184/
	│  │     │  ├─ 185/
	│  │     │  ├─ 186/
	│  │     │  ├─ 187/
	│  │     │  ├─ 188/
	│  │     │  ├─ 19/
	│  │     │  ├─ 191/
	│  │     │  ├─ 192/
	│  │     │  ├─ 195/
	│  │     │  ├─ 196/
	│  │     │  ├─ 197/
	│  │     │  ├─ 198/
	│  │     │  ├─ 199/
	│  │     │  ├─ 20/
	│  │     │  ├─ 200/
	│  │     │  ├─ 202/
	│  │     │  ├─ 203/
	│  │     │  ├─ 206/
	│  │     │  ├─ 209/
	│  │     │  ├─ 21/
	│  │     │  ├─ 210/
	│  │     │  ├─ 211/
	│  │     │  ├─ 212/
	│  │     │  ├─ 213/
	│  │     │  ├─ 214/
	│  │     │  ├─ 219/
	│  │     │  ├─ 22/
	│  │     │  ├─ 220/
	│  │     │  ├─ 221/
	│  │     │  ├─ 223/
	│  │     │  ├─ 225/
	│  │     │  ├─ 226/
	│  │     │  ├─ 227/
	│  │     │  ├─ 228/
	│  │     │  ├─ 229/
	│  │     │  ├─ 230/
	│  │     │  ├─ 233/
	│  │     │  ├─ 234/
	│  │     │  ├─ 237/
	│  │     │  ├─ 238/
	│  │     │  ├─ 239/
	│  │     │  ├─ 24/
	│  │     │  ├─ 240/
	│  │     │  ├─ 26/
	│  │     │  ├─ 27/
	│  │     │  ├─ 28/
	│  │     │  ├─ 29/
	│  │     │  ├─ 30/
	│  │     │  ├─ 32/
	│  │     │  ├─ 33/
	│  │     │  ├─ 34/
	│  │     │  ├─ 35/
	│  │     │  ├─ 36/
	│  │     │  ├─ 37/
	│  │     │  ├─ 4/
	│  │     │  ├─ 42/
	│  │     │  ├─ 43/
	│  │     │  ├─ 45/
	│  │     │  ├─ 46/
	│  │     │  ├─ 48/
	│  │     │  ├─ 49/
	│  │     │  ├─ 5/
	│  │     │  ├─ 50/
	│  │     │  ├─ 52/
	│  │     │  ├─ 53/
	│  │     │  ├─ 54/
	│  │     │  ├─ 55/
	│  │     │  ├─ 57/
	│  │     │  ├─ 58/
	│  │     │  ├─ 59/
	│  │     │  ├─ 6/
	│  │     │  ├─ 61/
	│  │     │  ├─ 62/
	│  │     │  ├─ 64/
	│  │     │  ├─ 65/
	│  │     │  ├─ 66/
	│  │     │  ├─ 67/
	│  │     │  ├─ 68/
	│  │     │  ├─ 69/
	│  │     │  ├─ 71/
	│  │     │  ├─ 73/
	│  │     │  ├─ 74/
	│  │     │  ├─ 75/
	│  │     │  ├─ 8/
	│  │     │  ├─ 80/
	│  │     │  ├─ 81/
	│  │     │  ├─ 82/
	│  │     │  ├─ 85/
	│  │     │  ├─ 88/
	│  │     │  ├─ 9/
	│  │     │  ├─ 90/
	│  │     │  ├─ 91/
	│  │     │  ├─ 94/
	│  │     │  ├─ 95/
	│  │     │  ├─ 96/
	│  │     │  ├─ 97/
	│  │     │  ├─ 98/
	│  │     │  └─ record.json
	│  │     ├─ stage-1/
	│  │     │  ├─ 0/
	│  │     │  ├─ 104/
	│  │     │  ├─ 107/
	│  │     │  ├─ 109/
	│  │     │  ├─ 110/
	│  │     │  ├─ 111/
	│  │     │  ├─ 113/
	│  │     │  ├─ 116/
	│  │     │  ├─ 117/
	│  │     │  ├─ 118/
	│  │     │  ├─ 119/
	│  │     │  ├─ 12/
	│  │     │  ├─ 121/
	│  │     │  ├─ 123/
	│  │     │  ├─ 126/
	│  │     │  ├─ 127/
	│  │     │  ├─ 136/
	│  │     │  ├─ 139/
	│  │     │  ├─ 147/
	│  │     │  ├─ 151/
	│  │     │  ├─ 153/
	│  │     │  ├─ 154/
	│  │     │  ├─ 16/
	│  │     │  ├─ 160/
	│  │     │  ├─ 161/
	│  │     │  ├─ 164/
	│  │     │  ├─ 165/
	│  │     │  ├─ 167/
	│  │     │  ├─ 168/
	│  │     │  ├─ 169/
	│  │     │  ├─ 173/
	│  │     │  ├─ 175/
	│  │     │  ├─ 176/
	│  │     │  ├─ 18/
	│  │     │  ├─ 183/
	│  │     │  ├─ 186/
	│  │     │  ├─ 188/
	│  │     │  ├─ 189/
	│  │     │  ├─ 19/
	│  │     │  ├─ 197/
	│  │     │  ├─ 198/
	│  │     │  ├─ 20/
	│  │     │  ├─ 200/
	│  │     │  ├─ 202/
	│  │     │  ├─ 203/
	│  │     │  ├─ 204/
	│  │     │  ├─ 205/
	│  │     │  ├─ 209/
	│  │     │  ├─ 21/
	│  │     │  ├─ 210/
	│  │     │  ├─ 22/
	│  │     │  ├─ 220/
	│  │     │  ├─ 223/
	│  │     │  ├─ 228/
	│  │     │  ├─ 230/
	│  │     │  ├─ 24/
	│  │     │  ├─ 240/
	│  │     │  ├─ 241/
	│  │     │  ├─ 243/
	│  │     │  ├─ 245/
	│  │     │  ├─ 249/
	│  │     │  ├─ 259/
	│  │     │  ├─ 260/
	│  │     │  ├─ 263/
	│  │     │  ├─ 264/
	│  │     │  ├─ 269/
	│  │     │  ├─ 27/
	│  │     │  ├─ 270/
	│  │     │  ├─ 272/
	│  │     │  ├─ 274/
	│  │     │  ├─ 28/
	│  │     │  ├─ 29/
	│  │     │  ├─ 30/
	│  │     │  ├─ 33/
	│  │     │  ├─ 36/
	│  │     │  ├─ 37/
	│  │     │  ├─ 43/
	│  │     │  ├─ 44/
	│  │     │  ├─ 45/
	│  │     │  ├─ 46/
	│  │     │  ├─ 48/
	│  │     │  ├─ 5/
	│  │     │  ├─ 50/
	│  │     │  ├─ 53/
	│  │     │  ├─ 55/
	│  │     │  ├─ 6/
	│  │     │  ├─ 60/
	│  │     │  ├─ 63/
	│  │     │  ├─ 67/
	│  │     │  ├─ 7/
	│  │     │  ├─ 70/
	│  │     │  ├─ 71/
	│  │     │  ├─ 79/
	│  │     │  ├─ 8/
	│  │     │  ├─ 84/
	│  │     │  ├─ 85/
	│  │     │  ├─ 90/
	│  │     │  ├─ 93/
	│  │     │  ├─ 96/
	│  │     │  └─ 98/
	│  │     ├─ stage-2/
	│  │     │  ├─ 0/
	│  │     │  ├─ 104/
	│  │     │  ├─ 107/
	│  │     │  ├─ 109/
	│  │     │  ├─ 110/
	│  │     │  ├─ 111/
	│  │     │  ├─ 113/
	│  │     │  ├─ 116/
	│  │     │  ├─ 117/
	│  │     │  ├─ 118/
	│  │     │  ├─ 119/
	│  │     │  ├─ 12/
	│  │     │  ├─ 121/
	│  │     │  ├─ 123/
	│  │     │  ├─ 126/
	│  │     │  ├─ 127/
	│  │     │  ├─ 136/
	│  │     │  ├─ 139/
	│  │     │  ├─ 147/
	│  │     │  ├─ 151/
	│  │     │  ├─ 153/
	│  │     │  ├─ 154/
	│  │     │  ├─ 16/
	│  │     │  ├─ 160/
	│  │     │  ├─ 161/
	│  │     │  ├─ 164/
	│  │     │  ├─ 165/
	│  │     │  ├─ 167/
	│  │     │  ├─ 168/
	│  │     │  ├─ 169/
	│  │     │  ├─ 173/
	│  │     │  ├─ 175/
	│  │     │  ├─ 176/
	│  │     │  ├─ 18/
	│  │     │  ├─ 183/
	│  │     │  ├─ 186/
	│  │     │  ├─ 188/
	│  │     │  ├─ 189/
	│  │     │  ├─ 19/
	│  │     │  ├─ 197/
	│  │     │  ├─ 198/
	│  │     │  ├─ 20/
	│  │     │  ├─ 200/
	│  │     │  ├─ 202/
	│  │     │  ├─ 203/
	│  │     │  ├─ 204/
	│  │     │  ├─ 205/
	│  │     │  ├─ 209/
	│  │     │  ├─ 21/
	│  │     │  ├─ 210/
	│  │     │  ├─ 22/
	│  │     │  ├─ 220/
	│  │     │  ├─ 223/
	│  │     │  ├─ 228/
	│  │     │  ├─ 230/
	│  │     │  ├─ 24/
	│  │     │  ├─ 240/
	│  │     │  ├─ 241/
	│  │     │  ├─ 243/
	│  │     │  ├─ 245/
	│  │     │  ├─ 249/
	│  │     │  ├─ 259/
	│  │     │  ├─ 260/
	│  │     │  ├─ 263/
	│  │     │  ├─ 264/
	│  │     │  ├─ 269/
	│  │     │  ├─ 27/
	│  │     │  ├─ 270/
	│  │     │  ├─ 272/
	│  │     │  ├─ 274/
	│  │     │  ├─ 28/
	│  │     │  ├─ 29/
	│  │     │  ├─ 30/
	│  │     │  ├─ 33/
	│  │     │  ├─ 36/
	│  │     │  ├─ 37/
	│  │     │  ├─ 43/
	│  │     │  ├─ 44/
	│  │     │  ├─ 45/
	│  │     │  ├─ 46/
	│  │     │  ├─ 48/
	│  │     │  ├─ 5/
	│  │     │  ├─ 50/
	│  │     │  ├─ 53/
	│  │     │  ├─ 55/
	│  │     │  ├─ 6/
	│  │     │  ├─ 60/
	│  │     │  ├─ 63/
	│  │     │  ├─ 67/
	│  │     │  ├─ 7/
	│  │     │  ├─ 70/
	│  │     │  ├─ 71/
	│  │     │  ├─ 79/
	│  │     │  ├─ 8/
	│  │     │  ├─ 84/
	│  │     │  ├─ 85/
	│  │     │  ├─ 90/
	│  │     │  ├─ 93/
	│  │     │  ├─ 96/
	│  │     │  └─ 98/
	│  │     ├─ stage-3/
	│  │     │  ├─ 0.txt
	│  │     │  ├─ 104.txt
	│  │     │  ├─ 107.txt
	│  │     │  ├─ 109.txt
	│  │     │  ├─ 110.txt
	│  │     │  ├─ 111.txt
	│  │     │  ├─ 113.txt
	│  │     │  ├─ 116.txt
	│  │     │  ├─ 117.txt
	│  │     │  ├─ 118.txt
	│  │     │  ├─ 119.txt
	│  │     │  ├─ 12.txt
	│  │     │  ├─ 121.txt
	│  │     │  ├─ 123.txt
	│  │     │  ├─ 126.txt
	│  │     │  ├─ 127.txt
	│  │     │  ├─ 136.txt
	│  │     │  ├─ 139.txt
	│  │     │  ├─ 147.txt
	│  │     │  ├─ 151.txt
	│  │     │  ├─ 153.txt
	│  │     │  ├─ 154.txt
	│  │     │  ├─ 16.txt
	│  │     │  ├─ 160.txt
	│  │     │  ├─ 161.txt
	│  │     │  ├─ 164.txt
	│  │     │  ├─ 165.txt
	│  │     │  ├─ 167.txt
	│  │     │  ├─ 168.txt
	│  │     │  ├─ 169.txt
	│  │     │  ├─ 173.txt
	│  │     │  ├─ 175.txt
	│  │     │  ├─ 176.txt
	│  │     │  ├─ 18.txt
	│  │     │  ├─ 183.txt
	│  │     │  ├─ 186.txt
	│  │     │  ├─ 188.txt
	│  │     │  ├─ 189.txt
	│  │     │  ├─ 19.txt
	│  │     │  ├─ 197.txt
	│  │     │  ├─ 198.txt
	│  │     │  ├─ 20.txt
	│  │     │  ├─ 200.txt
	│  │     │  ├─ 202.txt
	│  │     │  ├─ 203.txt
	│  │     │  ├─ 204.txt
	│  │     │  ├─ 205.txt
	│  │     │  ├─ 209.txt
	│  │     │  ├─ 21.txt
	│  │     │  ├─ 210.txt
	│  │     │  ├─ 22.txt
	│  │     │  ├─ 220.txt
	│  │     │  ├─ 223.txt
	│  │     │  ├─ 228.txt
	│  │     │  ├─ 230.txt
	│  │     │  ├─ 24.txt
	│  │     │  ├─ 240.txt
	│  │     │  ├─ 241.txt
	│  │     │  ├─ 243.txt
	│  │     │  ├─ 245.txt
	│  │     │  ├─ 249.txt
	│  │     │  ├─ 259.txt
	│  │     │  ├─ 260.txt
	│  │     │  ├─ 263.txt
	│  │     │  ├─ 264.txt
	│  │     │  ├─ 269.txt
	│  │     │  ├─ 27.txt
	│  │     │  ├─ 270.txt
	│  │     │  ├─ 272.txt
	│  │     │  ├─ 274.txt
	│  │     │  ├─ 28.txt
	│  │     │  ├─ 29.txt
	│  │     │  ├─ 30.txt
	│  │     │  ├─ 33.txt
	│  │     │  ├─ 36.txt
	│  │     │  ├─ 37.txt
	│  │     │  ├─ 43.txt
	│  │     │  ├─ 44.txt
	│  │     │  ├─ 45.txt
	│  │     │  ├─ 46.txt
	│  │     │  ├─ 48.txt
	│  │     │  ├─ 5.txt
	│  │     │  ├─ 50.txt
	│  │     │  ├─ 53.txt
	│  │     │  ├─ 55.txt
	│  │     │  ├─ 6.txt
	│  │     │  ├─ 60.txt
	│  │     │  ├─ 63.txt
	│  │     │  ├─ 67.txt
	│  │     │  ├─ 7.txt
	│  │     │  ├─ 70.txt
	│  │     │  ├─ 71.txt
	│  │     │  ├─ 79.txt
	│  │     │  ├─ 8.txt
	│  │     │  ├─ 84.txt
	│  │     │  ├─ 85.txt
	│  │     │  ├─ 90.txt
	│  │     │  ├─ 93.txt
	│  │     │  ├─ 96.txt
	│  │     │  ├─ 98.txt
	│  │     └─ summarization/
	│  │        ├─ 0.txt
	│  │        ├─ 104.txt
	│  │        ├─ 107.txt
	│  │        ├─ 109.txt
	│  │        ├─ 110.txt
	│  │        ├─ 111.txt
	│  │        ├─ 113.txt
	│  │        ├─ 116.txt
	│  │        ├─ 117.txt
	│  │        ├─ 118.txt
	│  │        ├─ 119.txt
	│  │        ├─ 12.txt
	│  │        ├─ 121.txt
	│  │        ├─ 123.txt
	│  │        ├─ 126.txt
	│  │        ├─ 127.txt
	│  │        ├─ 136.txt
	│  │        ├─ 139.txt
	│  │        ├─ 147.txt
	│  │        ├─ 151.txt
	│  │        ├─ 153.txt
	│  │        ├─ 154.txt
	│  │        ├─ 16.txt
	│  │        ├─ 160.txt
	│  │        ├─ 161.txt
	│  │        ├─ 164.txt
	│  │        ├─ 165.txt
	│  │        ├─ 167.txt
	│  │        ├─ 168.txt
	│  │        ├─ 169.txt
	│  │        ├─ 173.txt
	│  │        ├─ 175.txt
	│  │        ├─ 176.txt
	│  │        ├─ 18.txt
	│  │        ├─ 183.txt
	│  │        ├─ 186.txt
	│  │        ├─ 188.txt
	│  │        ├─ 189.txt
	│  │        ├─ 19.txt
	│  │        ├─ 197.txt
	│  │        ├─ 198.txt
	│  │        ├─ 20.txt
	│  │        ├─ 200.txt
	│  │        ├─ 202.txt
	│  │        ├─ 203.txt
	│  │        ├─ 204.txt
	│  │        ├─ 205.txt
	│  │        ├─ 209.txt
	│  │        ├─ 21.txt
	│  │        ├─ 210.txt
	│  │        ├─ 22.txt
	│  │        ├─ 220.txt
	│  │        ├─ 223.txt
	│  │        ├─ 228.txt
	│  │        ├─ 230.txt
	│  │        ├─ 24.txt
	│  │        ├─ 240.txt
	│  │        ├─ 241.txt
	│  │        ├─ 243.txt
	│  │        ├─ 245.txt
	│  │        ├─ 249.txt
	│  │        ├─ 259.txt
	│  │        ├─ 260.txt
	│  │        ├─ 263.txt
	│  │        ├─ 264.txt
	│  │        ├─ 269.txt
	│  │        ├─ 27.txt
	│  │        ├─ 270.txt
	│  │        ├─ 272.txt
	│  │        ├─ 274.txt
	│  │        ├─ 28.txt
	│  │        ├─ 29.txt
	│  │        ├─ 30.txt
	│  │        ├─ 33.txt
	│  │        ├─ 36.txt
	│  │        ├─ 37.txt
	│  │        ├─ 43.txt
	│  │        ├─ 44.txt
	│  │        ├─ 45.txt
	│  │        ├─ 46.txt
	│  │        ├─ 48.txt
	│  │        ├─ 5.txt
	│  │        ├─ 50.txt
	│  │        ├─ 53.txt
	│  │        ├─ 55.txt
	│  │        ├─ 6.txt
	│  │        ├─ 60.txt
	│  │        ├─ 63.txt
	│  │        ├─ 67.txt
	│  │        ├─ 7.txt
	│  │        ├─ 70.txt
	│  │        ├─ 71.txt
	│  │        ├─ 79.txt
	│  │        ├─ 8.txt
	│  │        ├─ 84.txt
	│  │        ├─ 85.txt
	│  │        ├─ 90.txt
	│  │        ├─ 93.txt
	│  │        ├─ 96.txt
	│  │        └─ 98.txt
	├─ response/
	│  ├─ .DS_Store
	│  └─ iteration-0/
	│     ├─ .DS_Store
	│     ├─ explanation/
	│     │  ├─ 0/
	│     │  ├─ 1/
	│     │  ├─ 10/
	│     │  ├─ 100/
	│     │  ├─ 101/
	│     │  ├─ 102/
	│     │  ├─ 103/
	│     │  ├─ 104/
	│     │  ├─ 105/
	│     │  ├─ 106/
	│     │  ├─ 107/
	│     │  ├─ 108/
	│     │  ├─ 109/
	│     │  ├─ 111/
	│     │  ├─ 112/
	│     │  ├─ 113/
	│     │  ├─ 114/
	│     │  ├─ 115/
	│     │  ├─ 117/
	│     │  ├─ 118/
	│     │  ├─ 119/
	│     │  ├─ 12/
	│     │  ├─ 120/
	│     │  ├─ 121/
	│     │  ├─ 123/
	│     │  ├─ 125/
	│     │  ├─ 126/
	│     │  ├─ 127/
	│     │  ├─ 128/
	│     │  ├─ 129/
	│     │  ├─ 13/
	│     │  ├─ 130/
	│     │  ├─ 131/
	│     │  ├─ 132/
	│     │  ├─ 133/
	│     │  ├─ 134/
	│     │  ├─ 135/
	│     │  ├─ 136/
	│     │  ├─ 138/
	│     │  ├─ 139/
	│     │  ├─ 14/
	│     │  ├─ 140/
	│     │  ├─ 141/
	│     │  ├─ 142/
	│     │  ├─ 143/
	│     │  ├─ 144/
	│     │  ├─ 145/
	│     │  ├─ 147/
	│     │  ├─ 148/
	│     │  ├─ 15/
	│     │  ├─ 150/
	│     │  ├─ 151/
	│     │  ├─ 152/
	│     │  ├─ 153/
	│     │  ├─ 154/
	│     │  ├─ 155/
	│     │  ├─ 157/
	│     │  ├─ 158/
	│     │  ├─ 159/
	│     │  ├─ 16/
	│     │  ├─ 161/
	│     │  ├─ 162/
	│     │  ├─ 163/
	│     │  ├─ 164/
	│     │  ├─ 167/
	│     │  ├─ 168/
	│     │  ├─ 169/
	│     │  ├─ 17/
	│     │  ├─ 171/
	│     │  ├─ 172/
	│     │  ├─ 174/
	│     │  ├─ 175/
	│     │  ├─ 176/
	│     │  ├─ 177/
	│     │  ├─ 178/
	│     │  ├─ 179/
	│     │  ├─ 18/
	│     │  ├─ 180/
	│     │  ├─ 181/
	│     │  ├─ 182/
	│     │  ├─ 183/
	│     │  ├─ 184/
	│     │  ├─ 185/
	│     │  ├─ 186/
	│     │  ├─ 187/
	│     │  ├─ 188/
	│     │  ├─ 19/
	│     │  ├─ 191/
	│     │  ├─ 192/
	│     │  ├─ 195/
	│     │  ├─ 196/
	│     │  ├─ 197/
	│     │  ├─ 198/
	│     │  ├─ 199/
	│     │  ├─ 20/
	│     │  ├─ 200/
	│     │  ├─ 202/
	│     │  ├─ 203/
	│     │  ├─ 206/
	│     │  ├─ 209/
	│     │  ├─ 21/
	│     │  ├─ 210/
	│     │  ├─ 211/
	│     │  ├─ 212/
	│     │  ├─ 213/
	│     │  ├─ 214/
	│     │  ├─ 219/
	│     │  ├─ 22/
	│     │  ├─ 220/
	│     │  ├─ 221/
	│     │  ├─ 223/
	│     │  ├─ 225/
	│     │  ├─ 226/
	│     │  ├─ 227/
	│     │  ├─ 228/
	│     │  ├─ 229/
	│     │  ├─ 230/
	│     │  ├─ 233/
	│     │  ├─ 234/
	│     │  ├─ 237/
	│     │  ├─ 238/
	│     │  ├─ 239/
	│     │  ├─ 24/
	│     │  ├─ 240/
	│     │  ├─ 26/
	│     │  ├─ 27/
	│     │  ├─ 28/
	│     │  ├─ 29/
	│     │  ├─ 30/
	│     │  ├─ 32/
	│     │  ├─ 33/
	│     │  ├─ 34/
	│     │  ├─ 35/
	│     │  ├─ 36/
	│     │  ├─ 37/
	│     │  ├─ 4/
	│     │  ├─ 42/
	│     │  ├─ 43/
	│     │  ├─ 45/
	│     │  ├─ 46/
	│     │  ├─ 48/
	│     │  ├─ 49/
	│     │  ├─ 5/
	│     │  ├─ 50/
	│     │  ├─ 52/
	│     │  ├─ 53/
	│     │  ├─ 54/
	│     │  ├─ 55/
	│     │  ├─ 57/
	│     │  ├─ 58/
	│     │  ├─ 59/
	│     │  ├─ 6/
	│     │  ├─ 61/
	│     │  ├─ 62/
	│     │  ├─ 64/
	│     │  ├─ 65/
	│     │  ├─ 66/
	│     │  ├─ 67/
	│     │  ├─ 68/
	│     │  ├─ 69/
	│     │  ├─ 71/
	│     │  ├─ 73/
	│     │  ├─ 74/
	│     │  ├─ 75/
	│     │  ├─ 8/
	│     │  ├─ 80/
	│     │  ├─ 81/
	│     │  ├─ 82/
	│     │  ├─ 85/
	│     │  ├─ 88/
	│     │  ├─ 9/
	│     │  ├─ 90/
	│     │  ├─ 91/
	│     │  ├─ 94/
	│     │  ├─ 95/
	│     │  ├─ 96/
	│     │  ├─ 97/
	│     │  ├─ 98/
	│     │  └─ record.json
	├─ metric_trace_log/
	│  └─ dataset/
	│     ├─ fine_tuning_narrow_few_shot_train_size_1.pkl
	│     ├─ narrow_few_shot_train_size_1.pkl
	│     ├─ narrow_few_shot_train_size_1_k_1_GPT4.pkl
	│     ├─ narrow_few_shot_train_size_1_k_1_random_labeling_12.pkl
	│     ├─ narrow_few_shot_train_size_1_k_1_random_labeling_24.pkl
	│     ├─ narrow_few_shot_train_size_1_k_1_random_labeling_36.pkl
	│     ├─ narrow_few_shot_train_size_1_k_1_random_labeling_48.pkl
	│     ├─ narrow_few_shot_train_size_1_k_1_random_labeling_60.pkl
	│     └─ narrow_few_shot_train_size_1_k_1_sre_corrections.pkl
	└─ selected_samples/
		└─ selected_samples_k_0.pkl
