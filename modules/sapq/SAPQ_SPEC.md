# 🛡️ SAPQ (Sequence Autonomic Parsing & QA) Engine Master Specification v1.0

> **Universal 4-Tier Contradiction Matrix & Multi-Directional Interleaved Cross-Parsing Audit Architecture**

---

## 🔮 4-Tier Contradiction Matrix (SAPQ 모순 검수 4단계 구조)

1. **Level 1: Structural & Topological Placement Contradiction (구조 및 배치 모순)**:
   - Hoisting order errors, reverse dependency line crossings (`TORSION_CROSSING`), and orphaned variables (`GHOST_NODE`).
2. **Level 2: Semantic State & Tensor Matrix Contradiction (상태 및 텐서 모순)**:
   - UI interlock desynchronization (`disabled`/`active` mismatch) and parameter schema channel mismatches.
3. **Level 3: Asynchronous Event Loop Timing Contradiction (비동기 타이밍 모순)**:
   - CDN module loading race conditions, async promise deadlocks, and 0ms render timing conflicts.
4. **Level 4: User Intent & Spec Alignment Contradiction (`INTENT_MISMATCH` - 유저 의도 및 구현 모순)**:
   - Cross-examines generated AST features against user prompt directives, task specifications, and original design goals.

---

# 📑 다방향 교차 파싱 기반 코드 무결성 자동 검수 엔진 명세서 (Multi-Directional Interleaved Cross-Parsing Audit Engine Spec)

---

## 📌 1. 개요 및 배경 (Overview & Motivation)

기존의 정적 코드 분석기(Linter / AST Parser)는 코드 베이스를 **단일 정방향 순차 시퀀스($A \rightarrow Z$)**로만 읽기 때문에, 비선형적 DOM 이벤트 꼬임, 이벤트 루프 사이의 상태 오염, 또는 드롭다운 인덱스 오차(`applyAutoLockL10` 등)와 같은 **다차원 로직 모순**을 검출하지 못하는 구조적 한계를 지닙니다.

본 명세서는 코드 첫 라인 A부터 끝 라인 Z를 기준으로 **정방향 파싱($A \rightarrow Z$), 역방향 파싱($Z \rightarrow A$), 스킵 정방향 파싱($a \rightarrow c \rightarrow e \dots$), 스킵 역방향 파싱($z \rightarrow x \rightarrow v \dots$)의 4단계 회차별 파싱 매트릭스**를 구축하고, 파싱 종료 시점(**Vector End Stage**)에서 각 회차별 명세표를 공간상 개별 토큰 노드로 배치한 뒤 **최종 궤적 선을 이어 통합 구조 검수**를 수행하는 **다방향 교차 파싱 검수 알고리즘 아키텍처**를 규정합니다.

> **💡 연산 비용 및 문맥 안전권 (Optimal Computational Safety Zone)**:
> 파싱 회차가 4단계를 초과할 경우 관계 복잡도가 $O(N^2)$으로 급증하여 연산 비용 폭발 및 LLM 문맥 단절(Context Truncation) 위험이 발생합니다. 따라서 본 대표자 정의 **4단계 시퀀스 파싱 파이프라인이 검수 정확도와 연산 효율성 간의 100% 최적 안전권(Sweet Spot)**을 구성합니다.

---

## 🧠 2. 4단계 교차 파싱 매트릭스 알고리즘 (4-Phase Interleaved Parsing Sequence)

```
[Phase 1: 정방향 파싱 (A ──► Z)] ───────────────► [토큰 노드 V1] ──┐
[Phase 2: 역방향 파싱 (Z ──► A)] ───────────────► [토큰 노드 V2] ──┼──► [Vector End: 궤적 선 연결(Line Linking)] ──► [모순점 100% 검출]
[Phase 3: 스킵 정방향 (a ──► c ──► e ...)] ─────► [토큰 노드 V3] ──┤
[Phase 4: 스킵 역방향 (z ──► x ──► v ...)] ─────► [토큰 노드 V4] ──┘
```

### 📊 [대표자 정의 4단계 파싱 시퀀스 명세표]

| 회차 (Phase) | 파싱 시퀀스 규칙 및 진행 패턴 | 검출 특화 버그 및 구조적 타깃 |
| :---: | :--- | :--- |
| **Phase 1 ($A \rightarrow Z$)** | **첫 라인 A부터 끝 라인 Z까지 순차 정방향 스캔** | 변수 호이스팅, 함수 정의 순서, 글로벌 딕셔너리 수집 |
| **Phase 2 ($Z \rightarrow A$)** | **끝 라인 Z부터 첫 라인 A까지 거꾸로 역방향 스캔** | 역의존성 불일치, 하위 렌더링 텐서 유실 및 고립 텐서 적발 |
| **Phase 3 ($a \rightarrow c \rightarrow e \dots$)** | **$A + (n+1)$ 규칙에 따른 스킵 정방향 파싱 ($Line_a \rightarrow Line_c \rightarrow Line_e \dots$)** | 겹치지 않는 규칙 스캔을 통해 중간 상태 누출 및 암묵적 종속 변수 적발 |
| **Phase 4 ($z \rightarrow x \rightarrow v \dots$)** | **$Z - (n+1)$ 규칙에 따른 스킵 역방향 파싱 ($Line_z \rightarrow Line_x \rightarrow Line_v \dots$)** | 역순 스킵 파싱을 통해 이벤트 루프 상태 오염 및 드롭다운 인덱스 밀림 적발 |

---

## 🌐 3. Vector End 시점 토큰 노드 배치 & 궤적 선 연결 메커니즘 (Vector Token Trajectory Linking)

### 🔮 **[1차: 회차별 파싱 명세표 ➔ 공간상 개별 토큰 노드 배치]**
* Phase 1부터 Phase 4까지 각 파싱 회차마다 생성되는 독자적인 결과 명세표를 공간상 **독립적인 3D/ND 토큰 노드($V_1, V_2, V_3, V_4$)**로 정밀 배치합니다.
* 노드 정보: 해당 회차 파싱에서 추출된 인덱스 맵, 함수 호출 순서, 글로벌 텐서 참조 맵.

### 🔗 **[2차: Vector End 시점 최종 궤적 선 연결 (Line Linking & Trajectory Fitting)]**
* Phase 4 스킵 역방향 파싱까지 모든 파싱 벡터의 노드 배치가 종료되는 시점(**Vector End Stage**)에서, 각 토큰 노드 간의 **의존성 궤적 선(Dependency Trajectory Lines)**을 최종 연결합니다.

```
[토큰 노드 V1 (A ──► Z)] ───────── (의존성 궤적 선 연결) ─────────► [토큰 노드 V2 (Z ──► A)]
          │                                                                  │
[토큰 노드 V3 (a ──► c)] ───────── (선 연결 단절 시 = 100% 버그 검출) ─────────► [토큰 노드 V4 (z ──► x)]
```

### 🔬 **[3차: 궤적 선 단절점 및 구조적 모순 검출 (Discontinuity & Contradiction Audit)]**
* 4대 토큰 노드의 연결 선을 잇는 과정에서 **선이 매끄럽게 연결되지 않고 끊어지거나(Discontinuity), 엉뚱하게 교차되는 지점(Torsion Crossing)**이 곧 버그의 정확한 위치입니다:
  1. **인덱스 오차 단절**: `dictMaster` 배열 노드와 `targetIdx` 노드 간 연결 선의 비틀림/단절 감지 (`applyAutoLockL10` 등 적발).
  2. **이벤트 무한 루프 교착**: 궤적 선이 닫힌 고리(Closed Loop)를 형성하여 무한 순환하는 지점 감지.
  3. **고립 토큰 노드 (Zombie Node)**: 어떤 연결 선도 도달하지 못하고 공중에 붕 뜬 좀비 변수/배열 감지 (`l07_cam_data_d2` 등 적발).

---

## 🚀 4. 적용 로드맵 및 실행 파이프라인

1. **1단계 (명세 수립)**: 대표자 정의 4단계 파싱 시퀀스($A \rightarrow Z, Z \rightarrow A, a \rightarrow c \rightarrow e, z \rightarrow x \rightarrow v$) 및 연산 비용 최적 안전권 명세 결착 완료.
2. **2단계 (파이썬 모듈 개발)**: SA-IR 전용 `multi_vector_parser.py` 자동 검수 툴 구현.
3. **3단계 (CI/CD 빌드 파이프라인 결착)**: `build_obfuscation.py` 실행 전 4단계 교차 파싱 및 궤적 선 연결 자동 수행 ➔ 무결성 통과 시에만 난독화 빌드 허용.

---

*본 명세서는 SA-IR 코드 무결성을 대표자 정의 4단계 파싱 시퀀스 및 Vector End 궤적 선 연결을 통해 연산 비용 안전권 내에서 완전하게 검증하기 위한 기술 명세서입니다.*


## 👑 Phase 16 Upgrade Directive: AST Node Tree & Dual-LLM AI-to-AI Semantic Cross-Audit Engine (`SAPQ v2.0`)

Google Jules must execute **Phase 16: Build Next-Gen AST Node Tree Parser & Dual-LLM AI-to-AI Semantic Cross-Auditor**:

### 🌳 16.1 Full AST (Abstract Syntax Tree) Node Tree Parser (`modules/sapq/sapq_ast_parser.py`)
- Transition from text/regex parsing to full **AST (Abstract Syntax Tree / ESTree Spec)** decomposition using Acorn / Babel / Python `ast`:
  - Decompose code into `Program` ➔ `FunctionDeclaration` ➔ `BlockStatement` ➔ `VariableDeclarator` ➔ `CallExpression` AST nodes.
  - **100% Mathematical AST Torsion Detection**: Compare AST `Identifier` usage node lines (`loc.start.line`) directly against `FunctionDeclaration` scope declaration lines.
  - **AST Mockup Hallucination Detection**: Inspect AST `ReturnStatement` nodes to detect static `Literal` returns or `Math.random()` pseudo-stubs with 0 dynamic I/O nodes.

### 🤖 16.2 Dual-LLM AI-to-AI Semantic Cross-Auditor (`modules/sapq/sapq_llm_auditor.py`)
- Deploy an independent **Auditor Agent LLM Gatekeeper** completely isolated from the Generator Agent:
  - **Cross-Verification Input**: Original User Prompt + AST Structural Feature Matrix + Generated Code.
  - **Semantic Intent Validation**: Audit whether the generated code fulfills 100% of user business logic or silently stubbed out endpoints (`SCOPE_REDUCTION`).
  - **Zero Self-Bias Guarantee**: Ensure independent dual-LLM cross-verification before approving any PR or live release!

## 🔍 Phase 18: Static DOM-Event Target Mismatch Parser & Relay (v1.1)
- Introduces `DOM_ID_DEF` capturing dynamically from `id="..."` declarations.
- Extends Phase 2 Backward parse to capture `DOM_EVENT_TARGET_REF` from strings inside inline events like `onclick="..."`.
- Dynamically audits and prevents **`EVENT_TARGET_MISMATCH`** where JS event calls target non-existent HTML IDs.

## 🧬 Phase 19: State Lifecycle & Cascade Mutation Graph (v2.0)
- **Cascade Graph:** Tracks Root State to Sub State dependency propagations via AST.
- **Blind Interceptor Detection:** Flags UI/DOM writes (`innerHTML`, `style`) occurring inside functions that never read from a master state context (`BLIND_INTERCEPTOR`), preventing untracked state mutations.
- **Temporal Lifecycle Lock:** Analyzes the global boot timeline to detect Data Races where render/update calls occur sequentially before initialization/boot calls (`TEMPORAL_LIFECYCLE_LOCK`).
