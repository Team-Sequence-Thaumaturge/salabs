# SAPQ 패치 재검증 보고서

**대상:** 사용자가 제공한 패치본 20개 모듈  
**검증 기준:** 이전 종합 분석에서 확인한 핵심 결함의 해결 여부, 새 통합 경로의 실제 동작, 회귀 위험  
**검증일:** 2026-08-16

## 결론

이번 패치는 **방향은 분명히 좋아졌습니다.** 특히 기존에는 기본 감사 경로 밖에 있던 인과성, 안티 목업, 캐스케이드 그래프, Python subprocess 검사를 `audit_file()`에 연결하고, CLI에 `--audit-only` 인자를 추가했으며, 전방 정의 정규식에 Python의 `def`와 `class`를 포함했습니다. 이로써 이전의 가장 큰 구조적 문제였던 “모듈은 있으나 실행되지 않음”은 **부분적으로 개선**되었습니다.

그러나 이번 패치는 **통합 폭을 넓힌 패치이지, 분석 정확성의 핵심 결함을 해결한 패치는 아닙니다.** 실제 회귀 검증에서 JavaScript 함수 호이스팅 오탐, Python AST 공개 메서드 예외, 다행 상태 불일치 누락, `--audit-only` 실행 실패, Phase 4 마지막 행 누락, 인터록의 새 보고서 키 무시, Level 4 LLM 감사 미연결이 그대로 확인되었습니다. 따라서 현재 상태는 “초기 프로토타입”에서 “여러 검출기가 연결된 알파 품질 게이트”로 올라갔지만, **자동 배포 차단의 신뢰 근거로 쓰기에는 아직 이릅니다.**

| 항목 | 이전 상태 | 패치 후 상태 | 판정 |
|---|---|---|---|
| 기본 경로의 모듈 통합 | Causality·Anti-mockup·Cascade 등이 미연결 | `audit_file()`에서 일부 호출·점수 반영 | **개선** |
| Python 선언 인식 | `def`/`class`를 V1에서 인식하지 못함 | V1 정의 수집은 가능 | **부분 개선** |
| JavaScript 함수 호이스팅 | `TORSION_CROSSING` 오탐 | 동일 오탐 재현 | **미해결** |
| Python AST 공개 API | `node.type` 접근으로 예외 | 동일 예외 재현 | **미해결** |
| Level 2 상태 불일치 | 미탐지 | 단일 행 문자열 패턴만 탐지 | **제한 개선** |
| Level 3 비동기 위험 | 이벤트 밀도 수준 | Cascade의 생명주기 휴리스틱 추가 | **부분 개선** |
| Level 4 LLM 의미 감사 | 모의 모듈·미연결 | 여전히 미연결 | **미해결** |
| `--audit-only` | 없음 | 옵션 추가, 실행 시 예외 | **회귀 결함** |
| 인터록과 보고서 스키마 | 키 불일치 | 핵심 새 키 여전히 무시 | **미해결** |

> **재검증 판정:** 병합 자체는 가능하지만, 배포 차단 모드의 기본 활성화는 보류해야 합니다. 아래의 P0 항목을 해결하고 회귀 테스트를 자동화한 뒤에 품질 게이트로 승격하는 것이 적절합니다.

## 1. 패치에서 실제로 좋아진 점

패치 변경은 20개 파일 중 `sapq_engine.py`, `sapq_ast_parser.py`, `sapq_cli.py` 세 파일에 집중되어 있습니다. `sapq_engine.py`는 이제 Phase 14 인과성, Phase 15 안티 목업, Phase 19 캐스케이드 그래프, Phase 17.3 사양 매처, Python 전용 subprocess 검사, HTML용 DOM 릴레이의 존재를 기본 경로에 연결합니다. 발견이 있으면 점수도 감점합니다.

실행 검증에서 다음 개선은 확인되었습니다.

| 검증 사례 | 실제 결과 | 해석 |
|---|---|---|
| 동일 행 `state.active = true; button.disabled = true;` | 85점, `CAUSALITY_CONTRADICTION` 1건 | 인과성 검출기 연결과 점수 감점이 작동합니다. |
| Promise 완료 전 `render()` 호출 | 80점, `TEMPORAL_LIFECYCLE_LOCK` 1건 추가 | 캐스케이드 검사기가 기본 보고서에 실제 포함됩니다. |
| 존재하지 않는 인라인 DOM ID | 80점, `EVENT_TARGET_MISMATCH` 1건 | 기존 Phase 18 기능이 유지됩니다. |
| 기준선에서 상태→DOM 역할을 제거 | 이전과 동일하게 `MISSING_INTENDED_FEATURE` 감점 | Phase 20 경로는 보존됩니다. |
| 전체 패치본 Python 컴파일 | 20개 모듈 컴파일 통과 | 최소한의 구문 무결성은 확보했습니다. |

이 변화는 작지 않습니다. 특히 검사 모듈을 최종 보고서와 점수에 연결한 것은 올바른 방향입니다. 다만 현재는 이들 모듈의 결과가 각각 다른 정밀도·다른 스키마·다른 의미를 가진 채 같은 점수에 합산됩니다. 다음 단계는 더 많은 모듈을 추가하는 것이 아니라 **증거 수준과 보고서 계약을 통일하는 것**입니다.

## 2. 이전 핵심 결함의 재검증 결과

### 2.1 JavaScript 함수 호이스팅 오탐은 그대로입니다 — P0

정상 JavaScript 코드인 아래 사례를 다시 검사했습니다.

```javascript
callLater();
function callLater() { return 42; }
```

결과는 여전히 90점과 `TORSION_CROSSING`입니다. 엔진은 참조 행이 선언 행보다 앞서는지 비교하지만, `FunctionDeclaration`은 JavaScript에서 호이스팅됩니다. 따라서 이 규칙은 기능 선언과 `let`/`const` TDZ, 함수 표현식, import 바인딩을 구분하지 못합니다. `sapq_engine.py:155-171`의 정규식 기반 행 순서 비교를 AST scope analysis로 대체해야 합니다.

### 2.2 Python AST의 공개 분석 메서드는 여전히 예외를 냅니다 — P0

Python 파일에서 `ASTParser.get_all_identifier_usages()`는 실행되지만, 다음 두 공개 메서드는 여전히 실패합니다.

| 메서드 | 실제 결과 |
|---|---|
| `detect_torsion_crossings()` | `AttributeError: 'Module' object has no attribute 'type'` |
| `detect_mockup_hallucinations()` | `AttributeError: 'Module' object has no attribute 'type'` |

원인은 `sapq_ast_parser.py:70-74` 및 `98-111`이 Python의 `ast.Module`, `ast.FunctionDef`, `ast.Return`에 대해 Esprima 전용의 `node.type`, `node.loc`를 그대로 접근하기 때문입니다. 패치된 Python 분기는 식별자 사용 수집에만 존재합니다.

더구나 새 구현은 `FunctionDef`와 `ClassDef`의 **선언 이름 자체를 usage 집합에 추가**합니다(`sapq_ast_parser.py:136-139`). 이로 인해 사용되지 않은 `unused_helper()`가 스스로 “사용됨”으로 간주되어 100점으로 통과했습니다. 이는 Python 지원을 개선했다기보다 **미사용 정의 탐지를 마스킹한 회귀**입니다.

### 2.3 다행 상태 불일치는 문자열 한 줄에서만 잡힙니다 — P1

아래처럼 일반적인 여러 행 상태 변경은 여전히 100점으로 통과했습니다.

```javascript
const state = { active: true };
if (state.active) {
  document.querySelector('#b').disabled = true;
}
```

반대로 `state.active = true; button.disabled = true;`처럼 같은 행에 두 표현식이 있을 때만 `CAUSALITY_CONTRADICTION`이 발생했습니다. 이는 `sapq_causality.py:50-58`의 단일 행 정규식 결과이며, 상태-UI 데이터 흐름 분석이 아닙니다. 따라서 Level 2의 “상태와 DOM 인터록 간 비동기적 불일치” 요구와는 여전히 큰 간극이 있습니다.

### 2.4 비동기 검출은 일부 개선됐지만, 핵심은 여전히 휴리스틱입니다 — P1

Promise 콜백 뒤에 `ready=true`가 설정되는데 그 전에 `render()`를 호출하는 사례에서 캐스케이드 모듈이 `TEMPORAL_LIFECYCLE_LOCK`을 추가로 검출했습니다. 이는 긍정적인 개선입니다. 다만 같은 사례는 함수 선언 호이스팅을 `TORSION_CROSSING`으로도 잘못 보고합니다.

또한 캐스케이드의 순서 판정은 함수 이름에 `init`, `load`, `fetch`, `setup`, `boot` 또는 `render`, `update`, `draw`, `paint`, `mount`가 포함되는지에 의존합니다. Promise/`await`/이벤트 리스너/타이머/마이크로태스크의 실제 의존성은 모델링하지 않습니다. **“레이스 후보 휴리스틱”**으로 보고하는 것은 가능하지만, “비동기 모순 확정” 점수로 강하게 감점하는 것은 과도합니다.

### 2.5 Level 4 의미 감사는 아직 기본 경로에 없습니다 — P1

`mockup_stub.js`의 아래 코드가 100점으로 통과했습니다.

```javascript
function pay() { return true; }
```

패키지의 `DualLLMAuditor`는 이 문자열 패턴을 의심할 수 있으나, 패치된 `sapq_engine.py`는 이를 import하거나 호출하지 않습니다. 연결된 `AntiMockupDepthEngine`도 일반 `return true;`가 아니라 특정 결제/암호화 관련 패턴을 주로 찾습니다. 즉, “LLM 교차 검증”은 여전히 명세상 기능이며 실제 기본 감사 기능이 아닙니다.

## 3. 이번 패치에서 새로 드러난 실행 결함

### 3.1 `--audit-only`는 실패하며, 비파괴 모드도 아닙니다 — P0

새 CLI 옵션 `--audit-only`는 점수가 100점 미만일 때 다음 예외로 종료됩니다.

```text
ValueError: Invalid state: AUDIT_ONLY_PENDING
```

엔진은 `sapq_engine.py:345-347`에서 `AUDIT_ONLY_PENDING` 상태로 전환하지만, `CheckpointManager.STATES`에는 그 값이 없습니다. 추가로 `audit_only=True`라도 `CheckpointManager`와 `SAPQLogger` 생성, 원본 백업 생성(`create_backup()`), 체크포인트·로그 기록은 옵션 처리보다 먼저 수행됩니다. 즉, 현재 구현은 **실행 실패**할 뿐 아니라, 성공하도록 고쳐도 곧바로 “비파괴 감사”가 되지는 않습니다.

권고는 다음과 같습니다.

1. `AUDIT_ONLY_PENDING`을 상태 열거형에 추가하거나, 감사 전용의 명확한 종료 상태를 정의합니다.
2. `audit_only`일 때 백업·상태 갱신·대상 디렉터리 쓰기를 하지 않거나, 별도 `--state-dir`에만 쓰도록 분리합니다.
3. 해당 모드를 CLI 통합 테스트로 고정합니다.

### 3.2 Phase 4는 홀수 행 파일의 마지막 이벤트를 놓칩니다 — P1

5행 파일의 마지막 5행에만 `setTimeout()`을 두고 검사한 결과, `V4_Skip_Backward_Count`가 0이었습니다. 원인은 `sapq_engine.py:106-113`의 시작 인덱스 계산입니다. 총 5행일 때 마지막 인덱스 4가 아니라 인덱스 3에서 시작합니다.

```python
# 현재 구조는 총 행 수가 홀수일 때 마지막 행을 건너뜁니다.
start_idx = self.total_lines - 1 if (self.total_lines - 1) % 2 == 1 else self.total_lines - 2
```

원래의 목적이 “끝 행에서 시작해 두 칸씩 역방향”이라면 아래처럼 단순해야 합니다.

```python
for idx in range(self.total_lines - 1, -1, -2):
    ...
```

### 3.3 인터록은 새로 통합된 핵심 보고서 키를 무시합니다 — P0

`SAPQInterlock.evaluate_audit_report()`는 `event_target_mismatches`, `python_subprocess_issues`, `cascade_graph_issues`를 계산하지 않습니다. 실제로 각각의 이슈만 넣은 보고서로 strict mode를 실행했지만 세 경우 모두 `True`를 반환하며 “Deployment approved”를 기록했습니다.

| 보고서에 포함한 단일 이슈 키 | strict mode의 실제 결과 |
|---|---|
| `event_target_mismatches` | 승인 |
| `python_subprocess_issues` | 승인 |
| `cascade_graph_issues` | 승인 |

이는 통합이 점수에만 반영되고, 최종 배포 차단의 계약에는 반영되지 않았음을 뜻합니다. 인터록은 명시적 허용 목록 대신 공통 severity 정책을 사용하거나, 최소한 엔진의 모든 이슈 배열을 포괄해야 합니다.

### 3.4 DOM 릴레이는 “실행됨”이 아니라 “인스턴스화됨”입니다 — P2

HTML 검사에서 `dom_relay_orchestrated=True`가 보고되지만, 엔진은 `SAPQDOMRelay(filepath)`를 생성할 뿐 `generate_navigation_map()`, `dispatch_event_and_capture()`, `execute_scenario()`를 호출하지 않습니다. 따라서 이 값은 런타임 DOM 검증의 성공이 아니라 객체 생성 여부입니다. 보고서 키를 `dom_relay_available`로 바꾸거나 실제 시나리오 실행 결과와 분리해야 합니다.

### 3.5 Spec matcher는 호출되지만 실질적으로 비활성입니다 — P2

엔진은 `SpecMatcher(filepath)`를 만들지만 specs 인자를 전달하지 않습니다. 이 모듈은 빈 specs에서 즉시 빈 목록을 반환하므로, 기본 경로의 사양 대조는 수행되지 않습니다. Python 파일에서는 JavaScript 파싱을 시도하며 `Spec Matcher Parsing Warning`도 출력됩니다. 사용자가 제공한 사양 파일·dict를 명시적으로 수신하고, Python 대상에서는 해당 matcher를 건너뛰거나 언어 어댑터를 제공해야 합니다.

## 4. 권고 우선순위

| 우선순위 | 조치 | 이유 | 완료 판정 |
|---:|---|---|---|
| P0 | `--audit-only` 상태·쓰기 정책 수정 | 새 공식 옵션이 실제 실패합니다. | 문제 파일에서도 종료 코드 0, 원본·대상 인접 경로에 새 파일 없음 또는 지정 state dir만 사용. |
| P0 | 인터록과 보고서 계약 통합 | 검출된 결함이 strict 배포 승인으로 통과합니다. | 엔진이 낼 수 있는 각 high/critical 이슈 키가 strict mode에서 차단됨. |
| P0 | Python AST 공개 메서드 분리 구현 | Phase 23 API가 예외를 내며 미사용 탐지를 스스로 무력화합니다. | Python/JS의 torsion·mockup·usage 테스트가 모두 예외 없이 통과. |
| P0 | 함수 선언 호이스팅 규칙 교정 | 정상 JS를 구조 결함으로 차단합니다. | FunctionDeclaration 선행 호출은 정상, `const`/함수 표현식의 실제 선행 참조는 별도 규칙으로 판정. |
| P1 | V4 시작 인덱스 수정 및 홀짝 테스트 | 명세의 4번째 벡터가 입력의 마지막 행을 놓칩니다. | 1~10행 모든 길이에서 대상 홀짝 위치가 정확히 스캔됨. |
| P1 | Level 2·3 결과의 confidence 분리 | 이름 기반/정규식 휴리스틱을 확정 결함처럼 다룹니다. | `heuristic`과 `proven`을 보고서·점수·인터록에서 다르게 처리. |
| P1 | LLM 감사의 명시적 연결 또는 기능 표기 수정 | 현재 Level 4는 구현 약속과 실행 현실이 다릅니다. | 실제 독립 감사 호출·구조화 출력·실패 정책, 또는 experimental/disabled 상태 명시. |
| P2 | DOM relay 결과 의미 수정 | 객체 생성이 E2E 검증 성공처럼 보입니다. | 사용된 시나리오, 성공·실패 step, 브라우저 오류가 보고서에 포함. |
| P2 | 사양 입력 인터페이스 설계 | 빈 사양으로 matcher를 부르면 아무 것도 검증하지 않습니다. | `--spec` 또는 API dict 입력과 언어별 적용 규칙이 존재. |

## 5. 최종 평가

이번 패치로 SAPQ는 **“분산된 모듈 모음”에서 “부분적으로 통합된 감사 파이프라인”으로 진전**했습니다. 인과성·캐스케이드·Python subprocess 결과를 점수에 반영한 것은 좋은 기반입니다. 따라서 이전 평가보다 분명히 높게 봅니다.

다만 품질 게이트의 핵심은 기능 수가 아니라 **오탐·누락·실행 실패·승인 규칙 사이의 일관성**입니다. 현재는 새 탐지기가 발견한 이슈가 인터록에서 무시되고, audit-only가 예외를 내며, Python AST의 공개 기능이 실패하고, 정상 JavaScript가 오탐됩니다. 이 네 가지는 먼저 닫아야 합니다.

> **권고 결론:** 이 패치는 계속 발전시킬 가치가 있으며, 코드 통합이라는 첫 단추는 잘 끼웠습니다. 다음 커밋은 새로운 Phase를 추가하지 말고, P0 네 항목을 고정 회귀 테스트와 함께 해결하는 “정확성·계약 안정화 릴리스”로 만드는 것이 가장 효과적입니다.

## 부록: 재현 산출물

| 파일 | 내용 |
|---|---|
| `sapq_patched_regression_output.json` | 패치본의 전체 회귀 실행 결과 |
| `sapq_patched_regression.py` | 실행한 최소 재현 테스트 |

모든 실행은 격리된 복사본에서 수행했으며, 패치 파일 자체는 수정하지 않았습니다.
