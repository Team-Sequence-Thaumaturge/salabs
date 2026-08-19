# SAPQ 신규 패치 재검증 보고서

**검증 대상:** 가장 최근에 첨부된 SAPQ 모듈 묶음만 사용  
**검증 목적:** 이전 회귀 결함의 해결 여부, ☒ 교차 검수 철학의 구현 충실도, 실행·인터록 계약 점검  
**검증일:** 2026-08-17

## 종합 판정

이번 패치는 **분명한 진전**입니다. 가장 중요한 두 회귀인 문법 오류 통과와 Phase 4 마지막 행 누락이 해결되었습니다. Python AST 파싱도 복구되었고, AST 기반 미선언 심볼 탐지와 모의 Level 4 감사가 기본 감사 경로에 연결되었습니다. 최신 패키지 20개 Python 모듈은 컴파일도 통과했습니다.

그러나 아직 “배포 차단 가능한 완성형 SAPQ”는 아닙니다. 정상 JavaScript 함수 선언 호이스팅은 여전히 `TORSION_CROSSING`으로 오탐되고, 상태·비동기 검출은 여전히 핵심 경로에서 작동하지 않으며, 인터록 호출은 메서드명 불일치로 실패합니다. 특히 미선언 심볼은 올바르게 발견하지만 점수·인터록에 반영되지 않아 100점으로 통과합니다. HTML 감사는 Playwright 브라우저 바이너리가 없으면 전체 감사 자체가 예외로 중단됩니다.

> **판정:** 직전 최신본의 “문법 오류 100점 통과” 상태에서는 확실히 벗어났습니다. 현재 버전은 **구조적 스캐너와 증거 수집기**로 의미가 생겼지만, ☒ 교차 검수의 핵심인 ‘독립된 관점의 증거를 하나의 신뢰 가능한 승인 규칙으로 결합’하는 단계는 아직 미완성입니다.

| 평가 영역 | 최신 결과 | 판단 |
|---|---|---|
| 문법 사전검사 | 잘못된 Python·JS가 0점 및 `preflight_status=FAILED` | **해결** |
| Phase 4 마지막 행 | 5행째 `setTimeout()`이 V4에 포함됨 | **해결** |
| Python AST 파싱 | Python `ast.parse`로 복구 | **부분 해결** |
| JS 함수 호이스팅 | 정상 FunctionDeclaration 선행 호출이 90점 | **미해결** |
| 미선언 심볼 탐지 | 검출은 성공하지만 100점 유지 | **부분 구현** |
| LLM/목업 경로 | `return true;`는 75점·`SCOPE_REDUCTION` | **부분 개선** |
| Level 2 상태 인터록 | 다행 상태 불일치를 100점으로 통과 | **미구현** |
| Level 3 비동기 레이스 | Promise 사례를 호이스팅 문제로 오탐 | **미구현** |
| 인터록 | 호출 메서드 불일치로 내부 실패 | **P0 결함** |
| HTML 런타임 릴레이 | 브라우저 미설치 시 감사 전체 예외 | **운영 결함** |
| `--audit-only` | 상태·로그 디렉터리 생성 | **비파괴 약속 불완전** |

## 1. 확인된 개선 사항

### 1.1 문법 오류 통과 회귀가 해결되었습니다

현재 `audit_file()`은 `SAPQPreflightGuard`를 먼저 호출합니다. 문법 오류 Python과 JavaScript 입력은 모두 다음과 같이 처리되었습니다.

| 입력 | 실제 결과 |
|---|---|
| `def broken(:` | 0점, `preflight_status=FAILED`, `SyntaxError: invalid syntax at L1` |
| `function broken( {` | 0점, `preflight_status=FAILED`, Esprima 구문 오류 |

이는 이전 버전에서 잘못된 코드를 100점 또는 98점으로 돌려주던 치명적 회귀를 해소한 것입니다. ☒ 검수의 모든 벡터는 최소한 파싱 가능한 코드라는 공통 전제를 가져야 하므로, 이 수정은 기능 추가보다 더 중요합니다.

### 1.2 Phase 4의 홀수 행 마지막 이벤트 누락이 해결되었습니다

`parse_phase_4_skip_backward()`이 이제 마지막 행 인덱스부터 `-2` 간격으로 순회합니다. 5행짜리 테스트의 마지막 5행에만 `setTimeout()`을 두었을 때 `V4_Skip_Backward_Count=1`이 반환됐습니다. 이는 역방향 스킵 벡터의 기본 규칙을 올바르게 복원한 것입니다.

### 1.3 Python AST 파서가 예외 없이 실행됩니다

`ASTParser`는 `.py` 파일에 Python 표준 `ast.parse`를 사용하고, Python 전용 torsion/mockup visitor를 별도 경로로 둡니다. 과거처럼 `ast.Module`에 Esprima 전용 `node.type`을 접근해 예외를 내지는 않았습니다.

다만 엔진의 V1/V2 정규식 벡터는 여전히 JavaScript 선언만 수집하므로, Python 함수의 정의·사용·좀비 노드 문제를 SAPQ의 4벡터 자체로 분석하는 상태는 아닙니다. 즉, **파서 안정성은 개선됐지만 다언어 교차 검수는 아직 완성되지 않았습니다.**

### 1.4 단순 모의 구현은 최소한 보고되기 시작했습니다

`function pay() { return true; }`는 최신 실행에서 75점과 `SCOPE_REDUCTION`으로 보고됐습니다. 이는 `DualLLMAuditor`가 기본 경로에 연결되어 작동한 결과입니다. 다만 호출 프롬프트가 실제 사용자 의도나 사양이 아니라 고정 문자열 `"Simulate prompt"`이므로, 아직 실제 의미 감사라고 보기는 어렵습니다.

## 2. 남은 P0 결함

### 2.1 엔진과 인터록의 메서드 계약이 깨져 있습니다

엔진은 다음과 같이 호출합니다.

```python
interlock.evaluate_audit_report(report, strict_mode=False)
```

하지만 최신 `InterlockCircuitBreaker`가 제공하는 메서드는 `evaluate_audit_results(results)`뿐입니다. 따라서 실행 결과마다 아래 오류 문자열이 `interlock_status`에 들어갔습니다.

```text
'InterlockCircuitBreaker' object has no attribute 'evaluate_audit_report'
```

이것은 배포 차단 로직이 현재 보고서를 신뢰성 있게 평가하지 못한다는 뜻입니다. 단순 alias로 클래스 이름만 맞춘 것으로는 충분하지 않고, **메서드명·입력 형태·strict mode 정책을 하나의 인터페이스로 통일**해야 합니다.

권고안은 다음 둘 중 하나입니다.

```python
# 단일 보고서용 메서드를 인터록에 명시적으로 둡니다.
def evaluate_audit_report(self, report, strict_mode=True):
    return self.evaluate_audit_results([report], strict_mode=strict_mode)
```

또는 엔진이 인터록의 현재 계약에 맞춰 리스트를 전달하도록 수정해야 합니다. 중요한 것은 어느 쪽이든 **통합 테스트로 고정**하는 것입니다.

### 2.2 미선언 심볼은 검출하지만 승인 규칙에 반영되지 않습니다

아래 정상 파싱 JavaScript에서 `unboundValue`는 정확히 `SCOPE_UNDECLARED_SYMBOL`로 검출되었습니다.

```javascript
function runner() {
  return unboundValue + 1;
}
runner();
```

그러나 결과 점수는 100점이었습니다. 원인은 두 가지입니다.

1. 초기 점수 계산에는 `scope_undeclared_symbols` 감점이 있으나, `audit_file()`의 최종 점수 재계산(`sapq_engine.py:309-320`)에는 이 항목이 빠져 있습니다.
2. 최신 인터록도 `scope_undeclared_symbols`를 차단 기준에 포함하지 않습니다.

따라서 “ReferenceError Trap”이라는 중요한 Level 1 발견이 보고서 장식으로만 남습니다. 최종 deductions와 interlock 모두에 같은 severity 정책으로 반영해야 합니다.

### 2.3 정상 JavaScript 함수 호이스팅 오탐이 지속됩니다

AST torsion 파서는 FunctionDeclaration을 호이스팅 예외로 처리하도록 개선되었습니다. 그러나 엔진의 정규식 기반 Phase 1/2 비교는 여전히 함수 선언을 정의로 넣고 선행 호출을 `TORSION_CROSSING`으로 기록합니다.

```javascript
callLater();
function callLater() { return 42; }
```

이 입력은 90점과 구조 모순 경고를 받았습니다. 따라서 AST와 정규식 결과가 여전히 서로 다른 의미론을 사용합니다. ☒ 구조에서는 이 같은 경우를 “두 관점의 모순”으로 다뤄야지, 정규식 결과만 결함으로 확정해서는 안 됩니다.

| 현재 상태 | 올바른 처리 |
|---|---|
| 정규식: 선행 참조 = 오류 | 정규식은 `HEURISTIC_FORWARD_REFERENCE` 후보만 생성 |
| AST: FunctionDeclaration 호이스팅 허용 | 의미론적 판정의 우선 근거 |
| 최종 결론: 오류 | `AST_CONFIRMED=false`이면 감점·차단하지 않고 보류/정보로 보고 |

## 3. Level 2·3과 ☒ 교차 검수의 남은 간극

### 3.1 상태 인터록은 아직 동작하지 않습니다

아래 다행 상태 불일치는 100점으로 통과했습니다.

```javascript
const state = { active: true };
if (state.active) {
  document.querySelector('#b').disabled = true;
}
```

현재 엔진은 `CausalityContradictionEngine`을 호출하므로 단일 행 패턴은 일부 검출할 수 있지만, 실제 다행 데이터 흐름·제어 흐름·DOM 속성 변이를 분석하지 않습니다. 특히 위와 같이 자주 쓰이는 여러 행 표현을 파악하지 못합니다.

### 3.2 비동기 레이스는 아직 “원인”이 아니라 호이스팅 오탐으로 보입니다

Promise 완료 전 `render()`가 호출되는 테스트는 90점과 `TORSION_CROSSING`만 보였습니다. `Promise`, `await`, 타이머, 이벤트 리스너의 happens-before 관계를 구축하는 분석기는 현재 핵심 경로에 없습니다.

이 지점이 SAPQ의 본질과 직접 연결됩니다. V4가 이벤트 행을 세는 것만으로는 “역방향에서 효과→원인 경로가 끊겼다”는 것을 보여주지 못합니다. Level 3은 다음과 같은 증거 단위가 필요합니다.

```text
render() at L3
  ← requires state.ready = true
  ← written in Promise continuation at L2
  ← no await / dependency edge before L3
  ⇒ RACE_CONDITION with trace
```

이런 evidence path가 있어야 다방향 검수가 단순 행 순회가 아니라 실제 역방향 인과 검수가 됩니다.

## 4. HTML/E2E와 audit-only의 운영상 결함

### 4.1 HTML 감사는 Playwright 실행 파일 부재 시 전체 실패합니다

HTML의 단순 DOM ID 불일치 테스트는 정적 검사를 마치기 전에 Playwright Chromium 실행 파일 부재로 예외가 발생했습니다. 현재 HTML 경로는 `dispatch_event_and_capture()`를 예외 격리 없이 호출하기 때문입니다.

런타임 E2E는 **선택적 보강 증거**여야 합니다. 따라서 Playwright가 준비되지 않았다면 정적 결과를 버리지 말고 다음처럼 보고해야 합니다.

```json
{
  "runtime_probe": {
    "status": "NOT_RUN",
    "reason": "Playwright browser binary unavailable"
  }
}
```

정적 DOM `EVENT_TARGET_MISMATCH`는 독립적으로 계속 제공되어야 합니다.

### 4.2 audit-only도 파일 시스템 부수 효과를 남깁니다

`audit_only=True`로 실행했는데 대상 디렉터리 아래 `.sapq_checkpoints`와 `.sapq_logs`가 생성됐습니다. 원인은 audit-only 분기보다 앞서 `CheckpointManager`와 `SAPQLogger`를 생성하고 `logger.log_session_start()`를 호출하기 때문입니다.

비파괴 모드의 계약을 지키려면 audit-only일 때 다음 중 하나가 필요합니다.

1. `NullCheckpointManager`와 `NullLogger`를 사용해 파일 쓰기를 완전히 없앱니다.
2. 모든 상태 산출물을 사용자가 별도로 지정한 `--state-dir`에만 보냅니다.
3. 최소한 `audit_only`가 “원본 내용만 불변”인지, “파일 시스템에도 쓰지 않음”인지 문서로 명확히 구분합니다.

## 5. 최신 버전의 ☒ 철학 평가

이번 버전에서는 다음 두 가지가 좋아졌습니다. 첫째, Phase 4의 실제 순회 오류가 고쳐졌습니다. 둘째, AST의 scope 검사가 “정규식으로 보이지 않는 미선언 심볼”이라는 다른 관점의 증거를 만들기 시작했습니다. 이것은 SAPQ의 교차 검수 철학에 더 가까워진 변화입니다.

하지만 Vector End는 아직 관점별 증거를 **교차 판정**하지 않습니다. 현재는 V1/V2의 정규식 결과, AST 결과, 외부 검출기 결과를 한 보고서와 감점식에 병렬로 더할 뿐입니다. 이 방식에서는 의미론적으로 더 강한 AST 결과가 정규식의 호이스팅 오탐을 반박해도, 최종 점수는 오탐을 그대로 채택합니다.

> **SAPQ의 다음 핵심 작업은 검출기 수를 늘리는 것이 아니라, 증거 간의 지지·반박·미확정을 표현하는 Vector End 판정기입니다.**

| 벡터/증거 | 현재 역할 | ☒에 맞는 다음 역할 |
|---|---|---|
| V1 정방향 | 선언 정규식 수집 | 선언·초기화·상태 생성 증거 |
| V2 역방향 | 식별자 정규식 수집 | DOM/API 효과에서 상태·호출 원인을 역추적 |
| V3 스킵 정방향 | 상태 행 개수 | 부분 그래프에서 불변식 검증 |
| V4 스킵 역방향 | 이벤트 행 개수 | 이벤트 효과→등록→초기화의 역방향 증거 |
| AST scope | 미선언 심볼 검출 | 정규식 후보를 확정·반박하는 의미론 증거 |
| Vector End | 감점 합계 | `CONFIRMED`, `REFUTED`, `INCONCLUSIVE` 판정 |

## 6. 우선순위 권고

| 우선순위 | 조치 | 완료 기준 |
|---:|---|---|
| P0 | 인터록 API 통일 | `audit_file()`의 `interlock_status`가 오류 없이 실제 정책 결과를 반환 |
| P0 | scope 미선언 심볼을 최종 감점·차단에 반영 | `unboundValue` 사례가 100점이 아니며 strict policy에서 차단 |
| P0 | 런타임 릴레이 실패 격리 | Playwright 미설치 HTML도 정적 보고서를 반환하고 runtime은 `NOT_RUN` |
| P1 | FunctionDeclaration 호이스팅 오탐 제거 | 정상 선행 호출은 `REFUTED` 또는 통과, 실제 TDZ만 경고 |
| P1 | audit-only의 무쓰기 보장 | `.sapq_*` 디렉터리·로그·백업이 생성되지 않음 |
| P1 | Python V1/V2 어댑터 | `def`, `class`, 이름 사용을 4벡터와 AST에 일관되게 반영 |
| P1 | 상태/비동기 증거 그래프 | 여러 행 상태 불일치와 Promise/await 레이스에 원인 경로 포함 |
| P2 | 실제 사양·프롬프트 입력 | 고정 `Simulate prompt` 대신 사용자 prompt/spec과 구조화된 audit context 사용 |

## 결론

이번 패치는 **기초 안정성 면에서 이전보다 더 좋습니다.** 문법 검사 복원, V4 인덱스 수정, Python AST 복구, scope detector 도입, 모의 intent gate 연결은 모두 유효한 개선입니다.

그러나 최종 승인 경로는 아직 묶이지 않았습니다. 지금은 “발견할 수 있는 것”과 “점수·인터록이 승인/차단하는 것”이 다릅니다. 다음 릴리스는 새 Phase를 추가하지 말고, **인터록 계약·scope 반영·HTML 런타임 격리·호이스팅 반박 판정**의 네 가지를 회귀 테스트와 함께 고정하는 안정화 릴리스가 되어야 합니다. 이 네 가지가 해결되면 SAPQ는 단순한 다중 스캐너를 넘어, 본래 의도한 ☒ 교차 증거 엔진으로 실제로 전진하게 됩니다.

## 부록: 재현 산출물

| 파일 | 내용 |
|---|---|
| `sapq_newest_regression_output.json` | 최신 코드 묶음의 원시 실행 결과 |
| `sapq_newest_regression.py` | 문법·호이스팅·Python·DOM·목업·V4·scope·audit-only 재현 스크립트 |

모든 검증은 사용자가 가장 최근에 업로드한 파일만 별도 디렉터리에 복사해 수행했습니다.
