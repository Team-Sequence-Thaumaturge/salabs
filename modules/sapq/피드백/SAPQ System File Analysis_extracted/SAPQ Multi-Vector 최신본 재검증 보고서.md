# SAPQ Multi-Vector 최신본 재검증 보고서

**대상:** 가장 최근에 첨부된 SAPQ 모듈 및 `multi_vector_parser.py`  
**목적:** 신규 다중 벡터 코어의 실행 가능성, 기존 엔진과의 통합, ☒ 교차 검수 구조의 실제 동작 검증  
**검증일:** 2026-08-17

## 결론

새 `multi_vector_parser.py`를 별도 추가한 방향 자체는 **정확합니다.** 기존 `sapq_engine.py` 안에 4방향 벡터와 여러 Phase를 섞어 두던 구조보다, 다방향 교차 파싱을 독립 코어로 분리하려는 시도는 SAPQ의 정체성을 더 잘 드러냅니다.

하지만 **현재 최신본은 패키지 import 단계에서 실패하므로 실행 가능한 릴리스가 아닙니다.** `sapq_ast_parser.py`에서 아직 정의되지 않은 `ASTMultiVectorParser`를 alias로 참조해 `NameError`가 발생합니다. 또한 이 오류를 임시로 우회하고 새 multi-vector 모듈만 독립 실행해도, 그 모듈은 기본 `audit_file()` 경로에 연결되어 있지 않습니다. 기존 엔진의 `MultiVectorCrossParsingAuditEngine` alias도 새 구현이 아니라 기존 `SAPQEngine`을 가리킵니다.

> **판정:** 설계 방향은 이전보다 SAPQ의 본질에 가까워졌지만, 현재는 “통합 전 초안 코어”입니다. 우선 import 오류와 단일 진입점 통합을 해결해야 하며, 그 전에는 성능·정확성 평가보다 릴리스 무결성 복구가 먼저입니다.

| 항목 | 결과 | 판정 |
|---|---|---|
| 22개 Python 파일 컴파일 | 통과 | 구문 수준 통과 |
| `import sapq_mv_latest` | `NameError: ASTMultiVectorParser` | **P0 실행 불가** |
| 새 multi-vector 코어 직접 실행 | 가능 | 독립 모듈 수준 동작 |
| 기본 `audit_file()`에 새 코어 연결 | 없음 | **P0 통합 누락** |
| 기존 alias | 기존 `SAPQEngine`을 가리킴 | **의도와 실제 불일치** |
| Phase 4 마지막 행 | 새 코어에서 다시 누락 | **회귀** |
| FunctionDeclaration 호이스팅 | 새 코어에서 90점 오탐 | **미해결** |
| async `.then` 혼용 | 이슈 생성, 점수는 100점 | **감점 계약 누락** |
| 다행 상태 불일치 | ghost node 1건만 보고 | **Level 2 미해결** |
| 인터록 API | 기존 엔진과 메서드 불일치 유지 | **P0 미해결** |

## 1. 먼저 해결해야 할 실행 차단 결함

### 1.1 AST alias 선언 순서가 잘못되었습니다

최신 `sapq_ast_parser.py`의 하단은 다음 순서입니다.

```python
# Backward compatibility alias
SAPQASTParser = ASTMultiVectorParser

# Backward compatibility aliases
ASTMultiVectorParser = ASTParser
SAPQASTParser = ASTParser
```

첫 줄에서 `ASTMultiVectorParser`는 아직 정의되지 않았으므로, 패키지 import가 즉시 중단됩니다. `compileall`은 이름 해석을 실행하지 않으므로 통과하지만, 실제 `import`와 CLI는 실패합니다.

수정은 한 줄의 선언 순서 정리입니다.

```python
ASTMultiVectorParser = ASTParser
SAPQASTParser = ASTParser
```

그리고 반드시 아래 두 런타임 테스트를 CI에 추가해야 합니다.

```bash
python -c "import sapq"
python -m sapq.sapq_cli --help
```

## 2. 신규 코어는 아직 기본 엔진의 일부가 아닙니다

`multi_vector_parser.py`에는 독립 `MultiVectorCrossParsingAuditEngine` 클래스가 있습니다. 그러나 `sapq_engine.py`는 이 모듈을 import하지 않습니다. 마지막 alias도 다음과 같습니다.

```python
MultiVectorCrossParsingAuditEngine = SAPQEngine
```

즉, 사용자나 다른 모듈이 `MultiVectorCrossParsingAuditEngine`이라는 이름으로 실제로 받는 객체는 새 코어가 아니라 예전 엔진입니다. 새 파일이 존재해도 운영·CLI·CI가 그것을 사용하지 않으므로, 현재 SAPQ 동작을 바꾸지 못합니다.

이 부분은 단순 import 추가보다 설계 결정을 먼저 내려야 합니다.

| 선택지 | 권고 |
|---|---|
| 새 모듈을 별도 실험 도구로 유지 | `experimental`로 명시하고 기본 엔진 alias를 제거 |
| 새 모듈을 SAPQ 코어로 채택 | `audit_file()`이 새 코어를 생성하고 결과를 공통 보고서 스키마로 변환 |
| 기존 엔진과 병렬 유지 | 두 결과를 `evidence_sources`에 저장하고 Vector End가 지지·반박을 판정 |

SAPQ의 ☒ 철학에는 세 번째 또는 두 번째가 더 맞습니다. 이름만 alias로 맞추는 방식은 가장 피해야 합니다.

## 3. 신규 multi-vector 코어의 실행 검증

패키지 alias 오류를 우회해 `multi_vector_parser.py`만 직접 로드하고 최소 사례를 실행했습니다.

| 사례 | 실제 결과 | 평가 |
|---|---|---|
| 정상 `FunctionDeclaration` 선행 호출 | 90점, `TORSION_CROSSING` | 정상 hoisting 오탐 |
| 5행째 `setTimeout()` | `V4_Skip_Backward_Count=0` | Phase 4 마지막 행 누락 회귀 |
| `await fetch().then()` | `ASYNC_TIMING_RACE` 생성, 총점 100 | 이슈가 감점에 미반영 |
| timeout 콜백 | `DUMMY_STATE_CONTRADICTION`, 95점 | 실제 타이머를 목업으로 오탐할 위험 |
| 여러 행 `active`/`disabled` | 98점, ghost node만 보고 | 상태 불일치 자체는 미탐 |

### 3.1 Phase 4 버그가 새 코어에서 다시 생겼습니다

새 코어는 다음처럼 시작 인덱스를 계산합니다.

```python
start_idx = self.total_lines - 1 if (self.total_lines - 1) % 2 == 1 else self.total_lines - 2
```

총 5행인 파일에서 마지막 index는 4인데 조건상 index 3부터 시작하므로 5행 이벤트를 건너뜁니다. 기존 `sapq_engine.py`에는 이미 더 정확한 구현이 있었지만, 새 모듈에는 이전 버전의 오류가 복사됐습니다.

정답은 간단합니다.

```python
for idx in range(self.total_lines - 1, -1, -2):
    ...
```

### 3.2 검출 결과와 점수의 계약이 일치하지 않습니다

`async_timing_contradictions`는 실제로 생성되지만 점수 계산에는 포함되지 않습니다. 따라서 async 이슈가 있는 사례가 100점이 됩니다. 이것은 이전의 `scope_undeclared_symbols` 감점 누락과 같은 범주의 문제입니다.

모든 검출기는 다음 공통 형식을 따라야 합니다.

```python
{
  "id": "ASYNC_TIMING_RACE",
  "severity": "warning",
  "confidence": "heuristic",
  "evidence": [...],
  "score_impact": 0,
  "interlock_policy": "warn"
}
```

그 후 **한 곳의 정책 테이블**만 점수와 interlock을 결정하도록 해야 합니다. 현재처럼 각 모듈에서 이슈를 만들고 다른 곳에서 일부 배열만 감점하면, 발견·점수·차단이 계속 어긋납니다.

### 3.3 Level 2와 Level 3은 아직 문자열 규칙입니다

새 코어의 Level 2는 `Math.random()`과 특정 `setTimeout` 형태를 찾는 정규식이고, Level 3은 같은 행에 `await`와 `.then(`이 함께 있을 때만 보고합니다. 이는 후보 탐지기로는 쓸 수 있지만, 상태·이벤트·의도 사이의 실제 모순을 뜻하지는 않습니다.

특히 아래 코드는 비동기 스타일 혼용일 수는 있어도 언제나 deadlock이나 race는 아닙니다.

```javascript
await fetch('/api').then(handle);
```

따라서 이 결과는 `HEURISTIC_WARNING`이어야 하며, 근거 없이 배포 차단할 수 없습니다. 반대로 진짜 race는 상태 write와 render/read 사이의 happens-before 경로가 끊기는지를 보여주는 증거 그래프가 필요합니다.

## 4. SAPQ 철학에 대한 현재 평가

이번 최신본에서 가장 긍정적인 변화는 **교차 파싱 자체를 독립 모듈로 이름 붙이고 외부화한 것**입니다. 이는 “단지 여러 규칙을 가진 린터”가 아니라, 정방향·역방향·부분 관점의 독립 증거를 Vector End에서 합치는 시스템이라는 정체성을 잘 보여 줍니다.

하지만 현재 구현은 4개의 벡터를 수집한 뒤 주로 V1/V2의 심볼 행 순서만 비교합니다. V3와 V4는 각각 문자열 행을 세고, 최종 결론에 거의 쓰이지 않습니다. 따라서 오늘의 multi-vector 코어는 **☒ 구조를 표현한 스캐폴드**이지, 아직 교차 반박을 수행하는 판정기까지는 아닙니다.

> 다방향성의 가치는 여러 번 스캔하는 횟수에 있지 않습니다. 한 벡터의 ‘그럴듯한 결론’을 다른 벡터가 독립 증거로 지지하거나 반박하게 만드는 데 있습니다.

이를 위해 Vector End는 단순 합산 대신 다음 세 상태를 가져야 합니다.

| Vector End 판정 | 의미 | 예시 |
|---|---|---|
| `CONFIRMED` | 서로 독립된 증거가 같은 결함을 지지 | AST scope와 역방향 사용 추적이 모두 미선언 심볼을 지지 |
| `REFUTED` | 강한 의미론 증거가 약한 휴리스틱을 반박 | AST가 FunctionDeclaration 호이스팅을 확인해 정규식 선행 참조 경고를 해제 |
| `INCONCLUSIVE` | 후보는 있으나 증거가 부족 | await/.then 혼용은 있으나 상태·렌더 인과 경로가 없음 |

이 방식은 SAPQ의 본질을 보존하면서 현재의 오탐 문제를 줄입니다.

## 5. 우선순위 권고

| 우선순위 | 조치 | 완료 기준 |
|---:|---|---|
| P0 | AST alias 선언 순서 수정 | `import sapq`와 CLI help가 성공 |
| P0 | 새 코어의 단일 진입점 결정 | `audit_file()`·CLI·alias가 실제 같은 multi-vector 구현을 사용 |
| P0 | 인터록 API 통일 | 단일 report와 report list 모두 계약된 메서드로 평가되며 오류 문자열 없음 |
| P1 | Phase 4 범위 수정 | 길이 1~10 파일의 마지막 홀짝 이벤트가 누락되지 않음 |
| P1 | 검출-점수-차단 정책 중앙화 | async/scope/DOM/intent 이슈가 공통 severity 표에 따라 일관되게 처리 |
| P1 | 호이스팅 반박 도입 | FunctionDeclaration 선행 호출은 `REFUTED`, 실제 TDZ만 `CONFIRMED` |
| P1 | V3/V4 evidence 활용 | 각 벡터가 상태·이벤트 원인 경로를 반환하고 Vector End가 교차 판정 |
| P2 | 실사용 prompt/spec 전달 | Level 4가 `Simulate prompt`가 아니라 실제 요구사항 입력을 받음 |

## 최종 결론

**좋은 방향 전환이지만, 지금은 실행 불가 상태입니다.** 새 `multi_vector_parser.py`는 SAPQ의 본질을 표현하려는 가장 적절한 출발점이지만, 기존 엔진에 연결되지 않았고 자체적으로 이전 회귀를 재도입했습니다.

다음 커밋의 목표는 새 Phase를 더 넣는 것이 아니라 다음 세 줄기를 닫는 것입니다.

1. 런타임 import와 CLI를 복구합니다.
2. 새 multi-vector 코어를 실제 감사 진입점으로 연결합니다.
3. Vector End가 정규식·AST·상태·비동기 증거를 `CONFIRMED / REFUTED / INCONCLUSIVE`로 판정하도록 만듭니다.

이 세 가지가 되면 SAPQ는 모듈 수가 많은 감사기가 아니라, 사용자가 의도한 **피상적 읽기를 교차 증거로 반박하는 검수 시스템**으로 실질적으로 전환됩니다.

## 부록: 재현 산출물

| 파일 | 내용 |
|---|---|
| `sapq_mv_core_regression_output.json` | 신규 multi-vector 코어 독립 실행 결과 |
| `sapq_mv_core_regression.py` | 4방향 벡터·호이스팅·V4·async·상태 재현 스크립트 |
| `sapq_mv_regression.py` | 정상 패키지 import 및 기본 엔진 통합 검증 시도 스크립트 |

모든 검증은 가장 최근 업로드된 파일만 별도 디렉터리에 복사해 수행했습니다.
