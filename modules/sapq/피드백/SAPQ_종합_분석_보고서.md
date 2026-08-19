# SAPQ 코드베이스 종합 분석 보고서

**대상:** 업로드된 SAPQ (Sequence Autonomic Parsing & QA) 구현 및 `SAPQ_SPEC.md`  
**분석일:** 2026-08-16  
**분석 범위:** 아키텍처, 실행 흐름, 명세 적합성, 정확성·보안·운영 품질, 제한된 재현 검증

## 결론 요약

SAPQ는 **정적 규칙 기반 프로토타입으로서는 일부 유의미한 기능을 갖추었지만, 현재 상태에서 “다방향 AST 기반 무결성 감사 엔진” 또는 CI/CD 배포 차단의 신뢰 근거로 사용하기에는 이릅니다.** 실제 기본 경로는 문법 사전검사, 정규식 기반 정의·참조 스캔, 간단한 DOM ID 대조, 선택적 기준선 역할 비교로 구성됩니다. 명세가 약속하는 상태 불일치, 비동기 레이스, 사용자 의도·LLM 교차감사, 인과성, 안티 목업 검사 등은 독립 모듈이거나 모의 구현이며, 기본 엔진과 CLI의 결과 보고서에 결합되지 않습니다.

가장 중요한 문제는 **점수의 신뢰성**입니다. JavaScript의 유효한 함수 선언 호이스팅을 `TORSION_CROSSING`으로 오탐했고, 상태-UI 불일치와 Promise 초기화 레이스는 100점 또는 구조적 경고만으로 통과했습니다. 또한 `.py` 대상의 전방 정의 벡터는 비어 있으며, 공개된 Python AST 기능 중 두 메서드는 실제 호출 시 예외를 발생시킵니다. 따라서 현재의 `audit_integrity_score=100`은 “명세상 네 단계 검증이 완료되었다”는 뜻으로 해석해서는 안 됩니다.

| 판정 항목 | 평가 | 핵심 근거 |
|---|---|---|
| 핵심 4회차 스캔 골격 | 부분 구현 | 전·역·스킵 전·스킵 역 토큰 수집은 존재하지만, V3는 보고용이고 V4는 이벤트 밀도만 사용합니다. |
| JavaScript/HTML의 단순 결함 탐지 | 제한적으로 유효 | 간단한 인라인 `onclick`의 미존재 ID는 재현 환경에서 검출했습니다. |
| AST 기반 구조·의미 분석 | 미완성 | AST 결과는 엔진에서 식별자 사용 집합 보정에만 사용되며, Python용 두 분석 메서드는 예외를 냅니다. |
| Level 2 상태 인터록 | 기본 경로 미구현 | `INTERLOCK_DESYNC`를 산출하거나 점수에 반영하는 경로가 없습니다. |
| Level 3 비동기 타이밍 | 기본 경로 미구현 | Promise·`async`·대기 그래프·실행 순서를 분석하지 않습니다. |
| Level 4 의도/이중 LLM 감사 | 모의·미연결 | `DualLLMAuditor`는 문자열 휴리스틱이며 엔진/CLI에서 호출되지 않습니다. |
| Phase 20 기준선 비교 | 제한적 구현 | 세 개 불리언 역할의 집합 차이는 작동하나 함수·호출 그래프·데이터 흐름 동형성은 보존하지 않습니다. |
| 운영 준비성 | 낮음 | 의존성 선언·테스트·패키징 메타데이터가 없고, 실행 시 소스 인접 경로에 백업·로그를 씁니다. |

> **종합 판정:** “기능 시연용 분석 보조 도구”로는 활용 가능하나, “자동 승인·차단의 단독 근거”로 사용하기에는 부적합합니다. 우선순위는 신규 탐지기를 더하는 것이 아니라, AST/언어 어댑터를 중심으로 기존 기능을 하나의 증거 모델과 하나의 보고서에 통합하는 것입니다.

## 1. 실제 아키텍처와 실행 흐름

표준 파일 감사는 `sapq_cli.py`에서 `audit_file()`로 진입합니다. 이 함수는 먼저 체크포인트와 JSONL 로그를 만들고, `SAPQPreflightGuard`로 문법을 확인한 다음 `SAPQEngine.execute_vector_end_trajectory_linking()`을 실행합니다. `--baseline`이 제공된 경우에만 `SAPQBaselineCube`가 추가됩니다. 이 경로에서 최종 보고서에 들어가는 것은 불연속성, 좀비 노드, DOM 이벤트 대상 불일치, 높은 이벤트 밀도, 그리고 선택적 기준선 누락입니다.

```text
CLI
 └─ audit_file()
     ├─ CheckpointManager / SAPQLogger  ← 대상 디렉터리에 부수 파일 생성
     ├─ SAPQPreflightGuard
     ├─ SAPQEngine
     │   ├─ V1: 정규식 정의·HTML id 수집
     │   ├─ V2: 정규식 식별자·인라인 onclick 문자열 수집
     │   ├─ V3/V4: 홀짝 행 기반 단순 토큰 수집
     │   └─ ASTParser.get_all_identifier_usages()만 보정 용도로 사용
     └─ SAPQBaselineCube (선택)
         └─ SAPQCascadeGraph의 3개 불리언 역할 집합 비교
```

반면 `DualLLMAuditor`, `SAPQDOMRelay`, `SAPQAgentProtocol`, `SAPQInterlock`, `CausalityContradictionEngine`, `AntiMockupDepthEngine`, `SpecMatcher`, `LiveProbeEngine`, `PythonASTParser`는 패키지에서 노출되거나 독립 실행이 가능하지만, 상기 기본 경로에는 결합되어 있지 않습니다. 정적 참조 검사에서도 `sapq_engine.py`와 `sapq_cli.py`는 DOM 릴레이, 이중 LLM, 인과성, 안티 목업, 인터록, 라이브 프로브, Python 전용 파서를 호출하지 않았습니다.

| 계층 | 실제 담당 모듈 | 구현 상태 | 평가 |
|---|---|---|---|
| 진입·보고 | `sapq_cli.py`, `sapq_engine.py` | 동작 | CLI 버전 표기는 v1.0, 엔진 docstring은 v1.1, 패키지는 v2.0으로 불일치합니다. |
| 사전검사 | `sapq_preflight.py` | 부분 동작 | Python은 `ast.parse`, JS는 Esprima, C/C++/Rust는 사실상 중괄호 수 확인입니다. |
| 4방향 토큰화 | `sapq_engine.py` | 부분 동작 | JavaScript 정규식 중심이며 토큰 간 의존성 그래프를 만들지 않습니다. |
| AST | `sapq_ast_parser.py` | 부분·결함 | Esprima/Python AST를 읽지만 분석 기능의 연결과 Python 호환성이 불완전합니다. |
| 기준선 | `sapq_baseline_cube.py`, `sapq_cascade_graph.py` | 제한 동작 | 역할의 존재/부재만 판단합니다. |
| 브라우저 E2E | `sapq_dom_relay.py`, `sapq_agent_protocol.py` | 독립 기능 | 기본 엔진과 보고서·인터록에 연결되지 않았고 Playwright 브라우저 준비도 누락됩니다. |
| 승인·차단 | `sapq_interlock.py`, `sapq_arbiter.py` | 독립 기능 | 인터록은 기본 보고서가 생성하지 않는 여러 키를 기대합니다. |

## 2. 명세 대비 적합성

`SAPQ_SPEC.md`는 네 파싱 벡터를 연결해 구조·상태·비동기·의도 모순을 검출하는 구조를 정의합니다. 구현에는 네 메서드가 존재하지만, “벡터 엔드에서의 의존성 궤적 연결”은 실제 그래프 구성이나 경로 분석이 아니라 사전형의 마지막 정의 행과 마지막 참조 행을 비교하는 방식입니다. V3 토큰은 최종 판정에 사용되지 않고, V4 토큰은 20개 초과 여부만을 `HIGH_EVENT_DENSITY`로 표시합니다. 따라서 선언·참조·상태·이벤트의 다방향 관계를 모델링하거나 실제 폐루프를 검증하는 구조는 아닙니다.

| 명세 요구 | 구현 근거 | 적합성 | 분석 |
|---|---|---:|---|
| Phase 1~4 순·역·스킵 파싱 | `sapq_engine.py:30-96` | 부분 | 네 스캔 함수는 있으나 대부분 정규식·문자열 포함 여부의 수집입니다. |
| Vector End 의존성 궤적·교차 | `sapq_engine.py:98-186` | 낮음 | 그래프·에지·경로·스코프 모델은 없고, 행 번호 선후 비교가 핵심입니다. |
| Level 1 구조 모순 | `sapq_engine.py:119-145` | 부분 | 간단한 미사용 정의와 선행 참조를 찾지만 JS 호이스팅 및 스코프를 고려하지 않습니다. |
| Level 2 UI interlock desync | 엔진 보고서 키 부재 | 없음 | `INTERLOCK_DESYNC` 탐지·산출·채점 경로가 없습니다. |
| Level 3 레이스·교착·0 ms 충돌 | `sapq_engine.py:160-166` | 매우 낮음 | 이벤트 개수만 확인하며 Promise, `await`, 콜백, 타이머 순서를 분석하지 않습니다. |
| Level 4 의도·명세 정합성 | `sapq_llm_auditor.py:14-40` | 없음/모의 | API 호출 없이 `TODO`, `Math.random()`, `return true;` 문자열만 검사하고 기본 경로에서 미호출입니다. |
| Phase 18 DOM 이벤트 대상 검증 | `sapq_engine.py:147-158` | 제한적 | 인라인 `onclick` 안 문자열만 보며 `addEventListener`, `querySelector`, 동적 ID는 놓칩니다. |
| Phase 19 상태·생명주기 그래프 | `sapq_cascade_graph.py:36-125` | 독립·휴리스틱 | 이름에 `state`·`data` 등이 포함되는지로 상태 읽기를 추정하며 기본 엔진이 부르지 않습니다. |
| Phase 20 동형 기준선 | `sapq_baseline_cube.py:26-130` | 제한적 | 3개 불리언 역할 서명의 집합 차이만 계산합니다. |
| Phase 21 자기치유·회로차단 | `sapq_arbiter.py:25-92` | 부분·독립 | 동일 점수의 반복만 진동으로 판단하고 실제 패치·검증 루프는 없습니다. |
| Phase 22 Playwright 시나리오 | `sapq_dom_relay.py:110-194` | 독립·부분 | 시나리오는 있으나 자동 감사·판정 경로에 통합되지 않았습니다. |
| Phase 23 Python AST 어댑터 | `sapq_ast_parser.py:45-163` | 결함 | 사용 추적 일부 외에는 JS 전용 `node.type` 접근으로 Python AST에서 예외가 납니다. |

## 3. 재현 검증 결과

컴파일 점검은 모든 업로드 Python 파일에서 통과했습니다. 다만 초기 환경에는 `esprima`와 `psutil`이 설치되어 있지 않았으며, 프로젝트에는 `requirements.txt`, `pyproject.toml`, `setup.py` 및 테스트 파일이 없었습니다. 따라서 깨끗한 환경에서 패키지를 설치·실행할 재현 가능한 계약이 제공되지 않습니다. 분석을 위해 격리 환경에 두 의존성을 별도 설치한 뒤, 아래 최소 사례를 실행했습니다.

| 재현 사례 | 기대되는 올바른 해석 | 실제 결과 | 판정 |
|---|---|---|---|
| `callLater(); function callLater(){}` | JavaScript 함수 선언은 호이스팅되므로 정상 | 90점, `TORSION_CROSSING` | **오탐** |
| Python의 미사용 `def unused_helper()` | Python 정의 벡터와 미사용 분석이 가능해야 함 | 100점, V1 정의 수 0 | **누락** |
| 인라인 `onclick`에서 존재하지 않는 ID 참조 | 대상 불일치 경고 | 80점, `EVENT_TARGET_MISMATCH` | **정상 검출** |
| `state.active`인데 버튼 `disabled=true` | Level 2 불일치 검토 | 100점, 문제 없음 | **누락** |
| Promise 완료 전 `render()` 호출 | 레이스/생명주기 위험 검토 | 90점, 함수 선행 참조만 보고 | **핵심 원인 누락** |
| 기준선의 상태→DOM 함수 삭제 | Phase 20 기능 누락 | 68점, `MISSING_INTENDED_FEATURE` | **제한적으로 정상** |
| Python `ASTParser.detect_torsion_crossings()` | Python AST 안전 분석 | `AttributeError: 'Module' object has no attribute 'type'` | **실행 결함** |
| Python `ASTParser.detect_mockup_hallucinations()` | Python AST 안전 분석 | 동일 `AttributeError` | **실행 결함** |
| `SAPQDOMRelay.generate_navigation_map()` | 로컬 E2E 기본 실행 | Playwright Chromium 실행 파일 부재 | **배포 준비 결함** |

특히 첫 사례는 위험합니다. `sapq_engine.py:131-145`는 참조 행이 정의 행보다 앞이면 구조 오류로 간주하지만, JavaScript의 함수 선언은 이 규칙의 예외입니다. 즉, 언어 의미를 파악하지 않는 행 번호 비교가 정상 코드를 결함으로 오인합니다. 반대로 Python 사례에서는 V1 정의 패턴이 `function|const|let|var`만 인정하므로 Python의 `def`가 한 건도 정의로 수집되지 않습니다. 이는 Phase 23의 다언어 지원 주장과 상충합니다.

## 4. 주요 결함 및 위험 우선순위

| 우선순위 | 심각도 | 발견 사항 | 영향 | 권고 조치 |
|---:|---|---|---|---|
| P0 | 높음 | 신뢰할 수 없는 점수·승인 근거 | 유효한 코드가 차단되고, Level 2/3 결함이 100점으로 통과할 수 있습니다. | 점수를 보류 상태로 바꾸고, 각 검출기의 증거·커버리지·미지원 언어를 별도 표기하십시오. |
| P0 | 높음 | Python AST API 예외 | 공개된 Phase 23 기능을 호출하면 실패합니다. | Python과 JS에 대해 공통 추상 노드를 만들거나 언어별 visitor를 분리하고, 모든 공개 메서드의 테스트를 추가하십시오. |
| P0 | 높음 | 기능 모듈의 미연결 | LLM, 인과성, 안티 목업, 인터록, DOM E2E가 기본 감사 결과에 반영되지 않습니다. | 단일 orchestration 파이프라인과 통합 보고서 스키마를 먼저 정의하십시오. |
| P1 | 높음 | 호이스팅·스코프 무시 | JavaScript 정상 동작의 오탐 및 `let`/`const`의 실제 TDZ 위험과 혼동이 발생합니다. | 정규식 행 비교를 AST scope analysis로 교체하고 선언 종류별 규칙을 분리하십시오. |
| P1 | 높음 | Phase 2/3 핵심 미구현 | 상태 불일치·Promise·콜백·타이머·이벤트 루프 문제를 실제로 판정하지 못합니다. | 데이터 흐름 그래프와 async call graph를 구축한 후, 검출기별 양성·음성 테스트를 만드십시오. |
| P1 | 중간 | 스킵 역방향 인덱스 오류 | 총 행 수가 홀수일 때 마지막 행을 시작점으로 삼지 않고 그 전 행부터 읽습니다. | `range(self.total_lines - 1, -1, -2)`로 단순화하고 홀수·짝수 파일 테스트를 추가하십시오. |
| P1 | 중간 | 경로 조작 가능성 | 공개 API의 `session_id`가 경로 검증 없이 체크포인트 파일명에 사용됩니다. 절대경로/상위경로 형태 입력은 의도하지 않은 위치에 쓰기를 유발할 수 있습니다. | `session_id`를 `[A-Za-z0-9_-]`로 제한하고 `Path.resolve()` 후 체크포인트 루트 하위인지 검증하십시오. |
| P1 | 중간 | 검사 실행의 소스 변경성 | 모든 감사가 대상 옆에 `.sapq_checkpoints`·`.sapq_logs`와 원본 백업을 생성합니다. | 기본값을 읽기 전용으로 두고, `--state-dir`·`--no-backup`·보존 정책·`.gitignore` 안내를 제공하십시오. |
| P2 | 중간 | 기준선 모델이 지나치게 거침 | 역할 서명이 세 불리언의 집합이어서, 한 함수가 같은 역할이면 여러 기준선 기능의 상실을 가릴 수 있습니다. | 함수 단위 다중집합, 호출자·피호출자, 상태 소스·DOM sink, AST 서브트리 특징을 포함하십시오. |
| P2 | 중간 | E2E 실행 준비 누락 | `playwright` 패키지 설치만으로 브라우저 바이너리가 설치되지 않습니다. | 잠금된 의존성 및 `playwright install --with-deps chromium` 문서/CI 단계를 제공하거나 시스템 Chromium 경로를 명시적으로 설정하십시오. |
| P2 | 중간 | 보고서 스키마 불일치 | 인터록은 `mockup_hallucinations`, `causality_contradictions`, `spec_mismatches` 등을 기대하나 기본 엔진은 생성하지 않습니다. | 버전이 관리되는 JSON Schema와 producer/consumer 계약 테스트를 도입하십시오. |
| P3 | 낮음 | DOM 릴레이 문자열 보간 | `fill`과 `assert_style`의 JavaScript 표현식에 입력을 직접 삽입합니다. 따옴표 입력이 실패하거나 페이지 문맥에서 의도하지 않은 코드를 만들 수 있습니다. | `locator.evaluate('(el, value) => { el.value = value; }', value)`처럼 인자를 분리하십시오. |
| P3 | 낮음 | 버전·용어 불일치 | 패키지 v2.0, CLI v1.0, 엔진 v1.1, 명세는 v1.0+v2.3 업그레이드를 함께 표기합니다. | 하나의 릴리스 버전, 기능 플래그, 호환성 매트릭스로 정리하십시오. |

## 5. 구현 품질 평가

### 강점

코드베이스는 관심사를 파일 단위로 분리했고, 사전검사·체크포인트·JSON 로그·기준선 비교·브라우저 시나리오라는 확장 지점을 제시합니다. 특히 단순한 인라인 DOM 대상 불일치와 기준선 역할의 완전 소실은 최소 사례에서 실제로 검출되었습니다. 체크포인트는 SHA-256으로 재개 전 파일 변경을 확인하며, 단계별 상태를 남깁니다.

또한 “무엇을 잡고 싶은가”는 명확합니다. 구조적 참조 오류, 상태-UI 불일치, 비동기 타이밍, 기능 누락, E2E 관찰을 하나의 품질 게이트로 묶으려는 방향은 타당합니다. 다만 현재 구현은 이러한 목표의 **공통 분석 중간표현(semantic IR)** 과 **통합 실행기**가 부족해, 개별 모듈의 존재가 실제 보장으로 이어지지 않습니다.

### 설계상 개선이 필요한 점

현재의 핵심 분석은 정규식에 의존합니다. 정규식은 빠른 보조 신호로는 적합하지만, 언어 문법·블록 스코프·클로저·import/export·클래스·동적 DOM·주석/문자열·JSX/TypeScript를 포함하는 “구조적 모순”의 결정 근거가 될 수 없습니다. 다음 개정에서는 분석을 **언어 어댑터 → 정규화 IR → 검출기 → 증거가 포함된 보고서** 구조로 재편하는 편이 안전합니다.

각 발견은 최소한 `rule_id`, `confidence`, `language`, `source_range`, `evidence`, `suppression_reason`, `detector_version`을 가져야 합니다. 그리고 “미지원” 또는 “분석 불가” 상태를 100점과 분리해야 합니다. 예를 들어 Python 함수를 V1에 전혀 넣지 못한 결과는 100점이 아니라 `INCONCLUSIVE`여야 합니다.

## 6. 권장 개선 로드맵

| 단계 | 목표 | 구체 조치 | 완료 기준 |
|---:|---|---|---|
| 1 | 신뢰성 회복 | 100점의 의미를 축소하고, 미지원·파싱 실패를 `INCONCLUSIVE`로 표기합니다. 세션 ID를 정규화하고 기본 실행을 read-only로 바꿉니다. | 정상 JS 함수 호이스팅이 오탐되지 않고, Python 미지원은 통과가 아닌 보류로 보고됩니다. |
| 2 | AST 코어 확립 | JavaScript와 Python visitor를 분리하고, 선언·참조·스코프·호출·DOM write·async 경계를 공통 IR로 정규화합니다. | Phase 1~4가 동일한 IR과 source range를 공유하며 Python 공개 API가 예외 없이 실행됩니다. |
| 3 | 실제 검출기 구현 | TDZ/호이스팅 구분, 미사용 심볼, DOM ID 참조, 상태→DOM 데이터 흐름, Promise/await/timer 의존성을 각각 구현합니다. | 규칙별 참양성·거짓양성·거짓음성 회귀 테스트가 존재합니다. |
| 4 | 기능 통합 | Cascade, baseline, anti-mockup, causality, LLM, DOM E2E를 옵션 기반 orchestration에 연결하고 공통 JSON Schema로 결합합니다. | 인터록이 실제 producer가 만든 모든 키를 소비하며, 누락 키는 명시적으로 `not_run` 처리됩니다. |
| 5 | 배포 가능성 | `pyproject.toml` 또는 명확한 requirements 잠금, Playwright 브라우저 설치 단계, 테스트·린트·타입 검사·CI를 추가합니다. | 깨끗한 환경의 단일 설치 명령과 CI에서 동일한 결과를 재현합니다. |
| 6 | LLM 기능의 정직한 도입 | 이중 독립 모델, 프롬프트/코드 경계, 구조화 출력, 실패 시 fail-closed 정책, 비용·개인정보 통제를 설계합니다. | 모의 구현 표기를 제거하고, 실제 호출 여부·모델 실패·데이터 전송을 보고서에 명시합니다. |

## 7. 즉시 적용 가능한 수정 우선순위

첫째, `parse_phase_4_skip_backward()`는 마지막 행에서 항상 시작하도록 고치고, `parse_phase_1_forward()`의 언어별 선언 수집을 AST로 대체해야 합니다. 둘째, `detect_torsion_crossings()`와 `detect_mockup_hallucinations()`의 Python 분기를 별도 구현해 `node.type` 접근을 제거해야 합니다. 셋째, 현재 호출되지 않는 검출기를 “지원 기능”으로 홍보하지 말고, 실행기에서 명시적으로 등록·실행·보고하거나 문서에서 실험 기능으로 분리해야 합니다.

넷째, `audit_integrity_score`는 구조적으로 재설계해야 합니다. 단순 감점식보다 **검출기별 실행 여부와 근거를 표시하는 다차원 결과**가 적절합니다. 예를 들어 `syntax=pass`, `scope_analysis=pass`, `async_analysis=not_run`, `intent_audit=not_run`처럼 제공하면, 사용자가 점수 100을 과대해석할 위험을 줄일 수 있습니다.

## 부록: 분석 산출물

본 분석에는 다음의 재현 결과가 포함됩니다.

| 파일 | 내용 |
|---|---|
| `sapq_review_smoke_output.json` | 함수 호이스팅, Python 미사용 정의, DOM ID, 상태/비동기, 기준선 비교의 실제 보고서 출력 |
| `sapq_feature_smoke_output.json` | Python AST 공개 메서드 예외와 Playwright 브라우저 실행 파일 누락 결과 |
| `sapq_review_smoke.py` | 주 감사 경로 재현 스크립트 |
| `sapq_feature_smoke.py` | AST·DOM 릴레이 독립 기능 재현 스크립트 |

**한 줄 권고:** SAPQ를 계속 발전시킬 가치는 있으나, 다음 릴리스의 성공 기준은 탐지 규칙 개수 증가가 아니라 **AST 기반 증거 모델, 언어별 정확성, 통합 보고서, 재현 가능한 테스트 체계**의 확립이어야 합니다.
