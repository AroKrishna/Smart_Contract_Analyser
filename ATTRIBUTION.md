# Attribution & Third-Party Notices — Smart Contract Analyser

This document details the licensing, attribution, and notices for project-owned code, third-party libraries, datasets, and pre-trained machine learning model weights included or referenced in **Smart Contract Analyser**.

---

## 1. Project-Owned Code

All original application code in this repository—including the React frontend, FastAPI backend services, analysis engine orchestration, report generators, and automated test suites—is authored by **AroKrishna** and licensed under the **MIT License**.

See [LICENSE](file:///c:/ARO/Projects/Smart_Contract_Analyser/LICENSE) for the full text of the MIT License.

---

## 2. Pre-Trained Deep Learning Base Model

The fine-tuned classification weights (`model.safetensors`, version `v3.3.0`) are fine-tuned from the pre-trained **LEGAL-BERT** foundation model:

- **Model**: `nlpaueb/legal-bert-base-uncased` (110M parameters)
- **Authors**: I. Chalkidis, M. Fergadiotis, P. Malakasiotis, N. Aletras, and I. Androutsopoulos
- **Publication**: *"LEGAL-BERT: The Muppets straight out of Law School"* (Findings of EMNLP 2020)
- **Upstream License**: **Apache License, Version 2.0**
- **Repository**: [https://huggingface.co/nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

The fine-tuned weights distributed via GitHub Releases are provided for research and academic evaluation purposes.

---

## 3. Machine Learning Datasets & Smart Contract Code Extracts

The canonical research dataset (`data/ml_candidates/final_dataset.jsonl`) contains metadata, natural-language AST summaries, and structural extracts from open-source smart contract repositories:

- **Permissive Open-Source Projects**: Contracts sourced from public repositories governed by permissive licenses (including **MIT**, **Apache-2.0**, **BSD-3-Clause**, and **ISC**) retain their respective upstream copyright and license notices.
- **Excluded / Restricted Licenses**: Contracts governed by non-permissive licenses (such as **BUSL-1.1** or **AGPL-3.0**) are explicitly tagged and excluded from the active training, validation, and testing splits (`training_eligible: false`, `split: "unassigned"`).
- **Synthetic Examples**: Synthetic training contracts (`SYN-001` through `SYN-020`) and sample demonstration files (`sample_contracts/manual_testing/`) were authored specifically for this research project and are licensed under the **MIT License**.

Detailed per-record provenance, repository URLs, and original commit hashes are fully documented in [docs/DATASET_SPECIFICATION.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/DATASET_SPECIFICATION.md) and [docs/DATASET_FINALIZATION_REPORT.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/DATASET_FINALIZATION_REPORT.md).

---

## 4. Key Third-Party Libraries & Frameworks

Smart Contract Analyser builds upon established open-source libraries:

### Backend (Python)
- **FastAPI**: Copyright (c) Sebastián Ramírez (MIT License)
- **PyTorch**: Copyright (c) Meta Platforms, Inc. and PyTorch contributors (BSD-3-Clause License)
- **Hugging Face Transformers**: Copyright (c) Hugging Face (Apache-2.0 License)
- **SHAP (SHapley Additive exPlanations)**: Copyright (c) Scott Lundberg (MIT License)
- **LIME**: Copyright (c) Marco Tulio Ribeiro (BSD-2-Clause License)
- **ReportLab**: Copyright (c) ReportLab Europe Ltd. (BSD License)
- **python-docx**: Copyright (c) Steve Canny (MIT License)
- **Pytest**: Copyright (c) Holger Krekel and pytest-dev team (MIT License)

### Frontend (JavaScript / React)
- **React**: Copyright (c) Meta Platforms, Inc. (MIT License)
- **Vite**: Copyright (c) Yuxi (Evan) You and Vite contributors (MIT License)
- **Tailwind CSS**: Copyright (c) Tailwind Labs, Inc. (MIT License)
- **Lucide Icons**: Copyright (c) Lucide Contributors (ISC License)
- **Recharts**: Copyright (c) Recharts Group (MIT License)

---

## 5. Non-Legal-Advice Disclaimer

Smart Contract Analyser is an automated academic research and decision-support tool. It does **not** provide legal advice, does **not** establish an attorney-client relationship, and does **not** guarantee judicial enforceability or statutory compliance across any legal jurisdiction. Always consult a qualified attorney for legal review of smart contracts.
