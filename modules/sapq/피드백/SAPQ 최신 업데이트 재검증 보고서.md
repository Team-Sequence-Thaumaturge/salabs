# SAPQ 최신 업데이트 재검증 보고서

**검증 대상:** 사용자가 마지막으로 지정한 최신 파일 묶음만 사용  
**검증 기준:** SAPQ의 ☒ 교차 검수 철학 보존, 이전 P0 결함의 해결 여부, 실제 실행·인터록 계약  
**검증일:** 2026-08-16

## 최종 판정

이 최신 묶음은 코드가 더 단순해지고 `audit_file()`이 대상 파일 옆에 체크포인트·로그·백업을 만들지 않는 **순수 읽기형 감사**로 바뀐 점은 좋습니다. 또한 현재 보고서 스키마에 맞춘 `InterlockCircuitBreaker`와 독립 실행 가능한 `SpecSemanticMatcher`도 갖췄습니다.

그러나 **현 상태는 직전 검증본보다 핵심 검출 범위가 축소되었고, 신뢰성도 낮아졌습니다.** 특히 사전 문법 검증, Python AST 지원, DOM 이벤트 대상 불일치, 상태 인터록, 캐스케이드/비동기 검사, 기준선 비교, LLM 의미 감사가 현재 `audit_file()` 경로에서 사라졌거나 실행되지 않습니다. JavaScript 함수 선언 호이스팅의 정상 사례는 이제 정규식과 AST에서 각각 한 번씩, 총 두 번의 `TORSION_CROSSING`으로 오탐되어 80점과 배포 차단을 받습니다. 반대로 문법 오류 Python은 100점, 존재하지 않는 DOM 이벤트 대상도 100점으로 통과합니다.

> **결론:** 최신 코드는 “비파괴적이고 간결한 Level 1 스캐너”로는 정리되었지만, SAPQ가 지향하는 **교차 증거 기반의 4계층 ☒ 검수기**로서는 현재 더 멀어졌습니다. 이 상태에서 CI/CD 배포 차단을 켜면 정상 JavaScript를 막고 실제 오류를 통과시키는 역전 현상이 발생합니다.

| 평가 영역 | 최신 결과 | 판정 |
|---|---|---|
| 대상 파일 부수 변경 | `audit_file()`이 파일 읽기와 보고서 반환에 집중 | **개선** |
| Python 문법·AST 지원 | Python을 Esprima로 파싱 시도 후 조용히 빈 AST 처리 | **심각한 회귀** |
| JS 함수 호이스팅 | 정규식·AST가 동일 정상 코드에 이중 오탐 | **미해결, 악화** |
| Level 2 상태 인터록 | 현재 엔진 경로에 검출기 없음 | **미구현** |
| Level 3 비동기 타이밍 | 현재 엔진 경로에 검출기 없음 | **미구현** |
| Level 4 사양·의도 | matcher는 독립 동작하나 엔진 입력·호출 없음; LLM 미연결 | **미구현** |
| Phase 4 스킵 역방향 | 홀수 행의 마지막 이벤트를 놓침 | **미해결** |
| 배포 인터록 | 현재 보고서 키는 소비하지만, 잘못된 탐지 결과를 강하게 차단 | **부분 개선, 위험** |

## 1. 실제로 좋아진 점

최신 `audit_file()`은 체크포인트·백업·로그를 만들지 않고 `SAPQEngine` 실행 결과만 돌려줍니다. 따라서 과거 `--audit-only` 상태값 오류나 “감사인데 원본 인접 경로를 수정한다”는 문제가 이 **현재 경로에서는 사라졌습니다.** 단, 이는 audit-only 옵션을 고친 것이 아니라 해당 옵션과 상태 관리 경로를 제거해 얻어진 효과입니다.

`InterlockCircuitBreaker`는 현재 엔진이 산출하는 `discontinuities_detected`, `zombie_nodes_detected`, `closed_loop_warnings`, `mockups_detected`, `python_popup_warnings`, `live_probe_failures`, `spec_alignment_warnings`를 검사합니다. 이전처럼 현재 보고서의 모든 키를 무시하고 무조건 승인하는 구조는 아닙니다.

`SpecSemanticMatcher`도 독립 실행에서는 동작했습니다. 예를 들어 `target frequency = 40`이라는 사양과 `const targetFrequency = 20` 코드 사이의 불일치를 `SPEC_ALIGNMENT_MISMATCH`로 반환했습니다. 이는 Level 4의 한 조각으로서 유효한 출발점입니다.

| 개선 항목 | 확인 내용 | 한계 |
|---|---|---|
| 비파괴 기본 감사 | 대상 옆 상태·백업 파일을 만드는 코드가 현재 `audit_file()`에 없음 | 문법 오류도 통과하므로 “안전한 감사”가 곧 “정확한 감사”는 아닙니다. |
| 인터록 스키마 | 현 보고서의 mockup/Python/probe/spec 키를 소비 | 실제 엔진이 Level 2·3·4 결과를 만들지 않아 범위가 제한됩니다. |
| 사양 대조기 | 독립 호출에서 값 불일치를 찾음 | 엔진은 `spec_warnings=[]`로 고정하며 matcher를 호출하지 않습니다. |

## 2. 실행 재현 결과

최신 파일만 별도 패키지로 구성해 20개 Python 모듈의 컴파일을 확인한 뒤, 최소 입력을 실행했습니다. 아래 표의 결과는 실제 출력에 근거합니다.

| 사례 | 기대되는 판단 | 최신 실제 결과 | 평가 |
|---|---|---|---|
| `callLater(); function callLater(){}` | 함수 선언 호이스팅으로 정상 | 80점, 정규식 `TORSION_CROSSING` + AST `AST_TORSION_CROSSING` 두 건 | **이중 오탐** |
| 사용되지 않은 Python `def` | Python 선언·사용 분석 또는 미지원 명시 | 100점, V1 정의 0, AST 파싱 경고 | **무음 누락** |
| 여러 행의 `active`/`disabled` 불일치 | Level 2 후보 보고 | 100점, 이슈 0 | **누락** |
| Promise 완료 전 `render()` | Level 3 레이스 후보 | 80점, 함수 선언 선행 참조 이중 오탐만 존재 | **핵심 원인 누락** |
| `function pay(){ return true; }` | 목업 후보 또는 보류 | 100점, 목업 0 | **누락** |
| 5행째 `setTimeout()` | V4 역스킵 벡터에 포함 | `V4_Skip_Backward_Count=0` | **누락** |
| 인라인 이벤트의 미존재 DOM ID | `EVENT_TARGET_MISMATCH` | 100점, 이슈 0 | **기능 소실** |
| 문법 오류 Python | preflight 실패 | 100점 | **심각한 회귀** |
| 문법 오류 JavaScript | preflight 실패 | 98점, ghost node만 보고 | **심각한 회귀** |

## 3. P0: 정상 JavaScript가 차단되고, 문법 오류가 통과합니다

### 3.1 함수 선언 호이스팅 이중 오탐

최신 엔진은 `sapq_engine.py:124-139`에서 정규식으로 만든 참조 행과 선언 행을 비교합니다. 이어 `sapq_ast_parser.py:49-77`도 함수 호출이 함수 선언보다 먼저 있으면 동일한 결론을 냅니다. 둘 다 JavaScript의 `FunctionDeclaration` 호이스팅을 고려하지 않습니다.

```javascript
callLater();
function callLater() { return 42; }
```

이 정상 코드는 두 탐지기에서 각각 감점되어 80점이 됩니다. 이어 CLI는 `InterlockCircuitBreaker`를 호출하므로 이 결과는 실제로 exit code 1의 배포 차단으로 이어졌습니다.

이 문제는 단순한 오탐이 아닙니다. SAPQ가 표방하는 “피상적 순방향 이해를 반대 관점에서 반박하는 검수”와 정반대입니다. **서로 독립적이어야 할 두 관점이 같은 행 번호 휴리스틱을 공유해 동일한 오해를 증폭**하고 있기 때문입니다. 이것은 ☒ 교차 검증이 아니라 상관된 중복 신호의 이중 계수입니다.

### 3.2 문법 오류 입력의 통과

현 엔진은 `SAPQPreflightGuard`를 import·호출하지 않습니다. `invalid_syntax.py`는 100점으로, `invalid_syntax.js`는 ghost node 감점만 받아 98점으로 반환되었습니다. 문법 오류를 “구조적으로 문제 없는 코드”와 같은 채널에서 점수화하면 이후 모든 교차 증거의 기반이 무너집니다.

우선순위는 새 탐지기를 추가하는 것이 아니라, **언어 파싱 실패를 `INVALID_INPUT` 또는 `INCONCLUSIVE`로 분리하는 것**입니다. 점수 0 또는 100으로 환원하지 말고, 인터록이 별도 정책으로 차단해야 합니다.

## 4. Python 지원은 예외 대신 침묵으로 바뀌었습니다

최신 `ASTParser`는 Python 파일을 구분하지 않고 Esprima `parseScript()`에 전달합니다. Python `def` 입력은 “Unexpected identifier” 경고를 남기고 AST를 `None`으로 둡니다. 그 후 torsion·mockup 메서드는 빈 목록을 반환하므로 호출 예외는 사라졌지만, 분석도 수행되지 않습니다.

엔진의 V1 선언 패턴도 JavaScript의 `function`, `const`, `let`, `var`, HTML `id`만 지원합니다. 따라서 Python `def`는 V1에 전혀 들어가지 않습니다. 최신 결과의 Python 100점은 “Python을 통과했다”가 아니라 **Python 분석이 비어 있었다**는 뜻입니다.

| 이전 문제 | 최신 상태 | 올바른 해결 |
|---|---|---|
| Python AST 메서드 예외 | 예외는 나지 않음 | Python `ast` 기반 visitor를 실제로 구현 |
| Python V1 정의 0건 | 그대로 0건 | `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, 할당을 언어 어댑터에서 수집 |
| Esprima 파싱 경고 | 경고 후 빈 결과 | Python 파일은 Esprima 경로에 절대 넣지 않음 |
| 100점 과신 | 그대로 발생 | `UNSUPPORTED_LANGUAGE`/`PARSE_FAILED`를 별도 상태로 보고 |

## 5. ☒ 교차 검수 철학과 현재 구현의 간극

사용자가 설명한 SAPQ의 본질은, 한 방향의 그럴듯한 읽기를 믿지 않고 정방향·역방향·부분 관점·기준선/사양 관점에서 **서로 독립된 반대 증거**를 만들어 결론을 교차 반박하는 것입니다. 이 목적은 여전히 유의미합니다.

하지만 최신 구현에서 V3는 단지 짝수 행의 `=`, `->`, 이벤트 속성 존재를 세고, V4는 이벤트 문자열을 포함한 행을 일부 수집한 뒤 20개 초과 여부만 봅니다. V3는 최종 결함 판정에 사용되지 않으며, V4도 실제 종속성·상태 전이·이벤트 순서를 분석하지 않습니다. 더 심각하게는 홀수 행 파일에서 시작 인덱스 계산 오류로 마지막 행 자체를 놓칩니다.

> **교차 검수의 유효 조건은 ‘방향의 수’가 아니라 ‘증거의 독립성’입니다.** 같은 행 순서 비교를 정규식과 AST에 중복 적용하면 오류를 상호 검증하는 것이 아니라 상호 증폭합니다.

따라서 SAPQ의 본질을 보존하려면 각 벡터를 다음처럼 정의해야 합니다.

| SAPQ 벡터 | 현재 최신 구현 | 철학을 보존하는 구현 |
|---|---|---|
| V1 정방향 | 정규식 선언 토큰 | AST 선언·초기화·상태 생성의 정방향 증거 그래프 |
| V2 역방향 | 정규식 식별자 토큰 | DOM 효과·API 응답·렌더 결과에서 상태·호출 원인을 역추적 |
| V3 스킵 정방향 | 격행 문자열 수집 | 연속 문맥을 제거한 부분 그래프에서 상태 불변식이 유지되는지 검사 |
| V4 스킵 역방향 | 격행 이벤트 문자열 수집 | 이벤트 효과에서 등록·초기화·취소 경로를 역방향으로 복원 |
| Vector End | 점수 합산 | 관점별 증거 그래프의 지지·모순·미확정 에지를 결합 |

## 6. Level 2·3·4는 현재 기본 경로에서 비어 있습니다

현재 엔진은 `AntiMockupDepthEngine`, `LiveProbeEngine`, `SpecSemanticMatcher`를 import하지만, `AntiMockupDepthEngine`은 인스턴스화하지 않고, live probe는 명시적으로 빈 배열로 비활성화하며, spec matcher도 `spec_warnings=[]`로 고정합니다. `DualLLMAuditor`, `SAPQCascadeGraph`, `CausalityContradictionEngine`, `SAPQDOMRelay`, `SAPQBaselineCube`는 최신 엔진 경로에 없습니다.

따라서 다음 기능은 명세 또는 별도 모듈에 존재하더라도 **현재 `audit_file()`의 실행 결과가 아닙니다.**

| 명세 계층 | 최신 기본 경로 상태 | 실제 영향 |
|---|---|---|
| Level 2 상태·UI 인터록 | 미호출 | 여러 행/함수/비동기 상태 불일치를 찾지 못함 |
| Level 3 Promise·타이머·이벤트 | 미호출 | 레이스를 함수 선언 선행 참조로 오해함 |
| Level 4 사용자 의도·LLM | 미호출 | `return true` 목업이 100점으로 통과 |
| DOM 이벤트 대상 | 미구현 | 미존재 ID 참조가 100점으로 통과 |
| 기준선 동형성 | 미호출 | 기능 소실을 비교하지 못함 |
| 사양 대조 | 독립 모듈만 존재 | CLI/엔진에 spec 입력 채널 없음 |

특히 `return true` 목업이 검출되지 않는 이유 중 하나는 AST 코드가 boolean literal을 Python 문자열 표현인 `"True"`로 바꾼 뒤 소문자 `"true"`와 비교하기 때문입니다. 그러나 더 근본적으로는 목업 판정이 의미적 근거 없이 매우 좁은 패턴에 의존한다는 점입니다.

## 7. 우선순위 권고

| 우선순위 | 조치 | 완료 조건 |
|---:|---|---|
| P0 | Preflight를 `audit_file()` 맨 앞에 복원 | 잘못된 JS/Python이 점수화되지 않고 `PARSE_FAILED`로 반환·차단됨 |
| P0 | 호이스팅 규칙 분리 | FunctionDeclaration 선행 호출은 통과, 함수 표현식/`let`/`const`의 실제 TDZ는 별도 판정 |
| P0 | Python 언어 어댑터 복원 | Python AST를 `ast.parse`로 분석하고, V1/V2·목업·미사용 분석이 Python에서 실제 실행 |
| P0 | 현재 엔진의 축소 여부를 결정 | Causality/Cascade/DOM/Baseline/LLM을 의도적으로 제외할지, 아니면 orchestration에 복원할지 명시 |
| P1 | V4 시작 인덱스 수정 | `range(total_lines - 1, -1, -2)` 및 길이 1~10 회귀 테스트 통과 |
| P1 | V3/V4의 증거 모델 도입 | 단순 행 수가 아닌 상태/이벤트 의존성 에지를 Vector End에 제공 |
| P1 | 사양 입력을 CLI/API로 연결 | `--spec` 또는 JSON spec을 받아 `SpecSemanticMatcher` 결과가 실제 보고서와 인터록에 반영 |
| P1 | 분류·점수 정책 분리 | `PROVEN`, `HEURISTIC`, `INCONCLUSIVE`, `UNSUPPORTED`를 점수와 별도로 표시 |
| P2 | 인터록의 정책 강화 | 신뢰도 낮은 관찰은 경고, 문법 오류·검증된 고위험 이슈만 기본 차단 |

## 결론: 다음 커밋의 목표

다음 커밋은 새 Phase나 새 모듈을 추가하는 것이 아니라 **“교차 검수의 독립성 회복”**이어야 합니다. 최소한 다음 네 가지가 동시에 만족되어야 합니다.

1. 정상 JavaScript 호이스팅이 차단되지 않는다.
2. 잘못된 문법과 미지원 언어는 100점이 아니라 `INCONCLUSIVE` 또는 `PARSE_FAILED`가 된다.
3. V1~V4가 각자 다른 증거 그래프를 만들고, Vector End가 그 증거의 모순을 판정한다.
4. 배포 인터록은 검증된 고위험 이슈를 차단하되, 단순 휴리스틱을 확정 결함처럼 이중 계수하지 않는다.

이 네 조건을 달성하면 SAPQ의 본질, 즉 LLM이나 사람이 한 번 훑고 “그럴듯하다”고 승인하는 것을 막기 위한 ☒ 교차 검수 철학은 훼손되지 않습니다. 오히려 현재보다 훨씬 명확하게 구현됩니다.

## 부록: 실행 산출물

| 파일 | 내용 |
|---|---|
| `sapq_latest_regression_output.json` | 최신 패키지의 회귀 실행 원시 결과 |
| `sapq_latest_regression.py` | 실행한 최소 재현 테스트 |

모든 검증은 사용자가 지정한 마지막 최신 파일만 별도 디렉터리에 복사해 수행했습니다.
