# SAPQ 최신본 재검증 결과

**대상:** 가장 최근에 제공된 SAPQ 코드 묶음  
**검증일:** 2026-08-17  
**초점:** multi-vector 통합, non-strict interlock, audit-only, V4·호이스팅·async 회귀

## 결론

최신본은 **패키지 import와 CLI 실행은 정상**입니다. 그러나 직전 검증에서 지적한 핵심 구조 문제는 현재 최신 파일의 `sapq_engine.py`, `multi_vector_parser.py`, `sapq_interlock.py`에 그대로 남아 있습니다. 따라서 이번 묶음은 실행 가능하지만, multi-vector 중심 SAPQ로의 전환이나 라이브러리 안전성 측면에서 의미 있는 추가 개선은 확인되지 않았습니다.

| 검증 항목 | 실제 결과 | 판정 |
|---|---|---|
| Python 컴파일 | 전체 모듈 통과 | 통과 |
| 패키지 import | 성공 | 통과 |
| CLI `--help` | 성공 | 통과 |
| 기본 엔진의 함수 hoisting | 100점·승인 | 이전 개선 유지 |
| multi-vector의 함수 hoisting | 90점·`TORSION_CROSSING` | 미해결 |
| multi-vector의 마지막 행 V4 | 5행 이벤트를 놓침 | 미해결 |
| multi-vector async 이슈 | 이슈 생성, 점수 100 | 정책 단절 |
| 기본 engine의 multi-vector 사용 | 호출/통합 없음 | 미해결 |
| non-strict interlock | `SystemExit(1)` | P0 미해결 |
| audit-only | `.sapq_checkpoints`, `.sapq_logs` 생성 | 미해결 |

## 1. 실행성은 정상입니다

최신본을 별도 패키지로 구성한 뒤 전체 Python 컴파일, `import sapq_final_latest`, `python -m sapq_final_latest.sapq_cli --help`를 실행했습니다. 세 검증은 모두 통과했습니다. 이전의 alias 선언 순서로 인한 import 실패는 현재 재발하지 않았습니다.

또한 기본 엔진의 JavaScript FunctionDeclaration 호이스팅 보정도 유지됩니다. 다음 정상 코드는 기본 `audit_file()` 경로에서 100점으로 통과했습니다.

```javascript
callLater();
function callLater() { return 42; }
```

이 점은 긍정적입니다. 다만 이 보정은 기본 `SAPQEngine`에만 있고, 새 multi-vector 코어에는 반영되어 있지 않습니다.

## 2. multi-vector 코어는 아직 기본 경로에 연결되지 않았습니다

최신 `sapq_engine.py`는 `multi_vector_parser.py`를 import하거나 인스턴스화하지 않습니다. 마지막 alias도 다음과 같습니다.

```python
MultiVectorCrossParsingAuditEngine = SAPQEngine
```

따라서 CLI와 `audit_file()`이 실제로 사용한 엔진은 새 `multi_vector_parser.MultiVectorCrossParsingAuditEngine`이 아닙니다. 새 코어는 파일로 존재하지만 운영 감사·점수·interlock에는 참여하지 않습니다.

이로 인해 두 구현의 행동이 분기됩니다.

| 동일 사례 | 기본 엔진 | 새 multi-vector 코어 |
|---|---|---|
| 정상 FunctionDeclaration 선행 호출 | 100점, 통과 | 90점, hoisting 오탐 |
| V4 마지막 행 이벤트 | 기본 engine V4는 올바른 순회 코드 | V4 count 0, 마지막 행 누락 |
| async 혼용 | 별도 core 결과 미사용 | 이슈를 만들지만 점수 100 |

> 새 코어가 SAPQ의 정체성을 표현한다면, 다음 커밋의 최우선 작업은 이를 `audit_file()`의 실제 orchestration에 연결하는 것입니다. 그렇지 않다면 명시적으로 experimental 도구로 표시해야 합니다.

## 3. V4와 async 점수 계약은 새 코어에서 여전히 깨져 있습니다

### 3.1 V4 마지막 행 누락

5행째에만 `setTimeout()`을 둔 입력에서 multi-vector 결과는 `V4_Skip_Backward_Count=0`이었습니다. 원인은 다음 시작 인덱스 계산입니다.

```python
start_idx = self.total_lines - 1 if (self.total_lines - 1) % 2 == 1 else self.total_lines - 2
```

총 5행일 때 마지막 index 4가 아니라 3부터 시작합니다. 아래와 같이 단순화해야 합니다.

```python
for idx in range(self.total_lines - 1, -1, -2):
    ...
```

### 3.2 async 발견은 점수에 반영되지 않습니다

```javascript
await fetch('/api').then(handle);
```

이 입력에서 multi-vector 코어는 `ASYNC_TIMING_RACE` 이슈를 생성했지만 총점은 100입니다. 해당 배열이 report에는 존재하지만 score 수식에는 포함되지 않기 때문입니다.

다만 이 패턴은 확정 race가 아니라 후보일 수 있습니다. 따라서 단순 감점 추가보다는 다음과 같은 공통 정책이 바람직합니다.

| 판정 | 예시 | 기본 처리 |
|---|---|---|
| `CONFIRMED` | 문법 오류, scope 미선언 | 차단 |
| `REFUTED` | FunctionDeclaration hoisting | 감점·차단 없음 |
| `INCONCLUSIVE` | await/.then 혼용 | 경고 및 추가 증거 요구 |

## 4. non-strict interlock은 여전히 호출자를 종료합니다

`SAPQInterlock.evaluate_audit_report(report, strict_mode=False)`를 직접 호출해도, scope 이슈가 있으면 `SystemExit(1)`가 발생했습니다. 이 값은 현재 API에서 실제로 사용되지 않습니다.

같은 이유로 `audit_file(..., audit_only=True)`도 이슈를 발견하면 결과 report를 반환하지 않고 프로세스를 종료합니다. 이는 라이브러리 API·에이전트·웹 서버·테스트 러너에 부적절한 계약입니다.

```python
# 필요한 방향
if not approved:
    if strict_mode:
        raise DeploymentBlocked(decision)
    return decision
```

CLI의 최상단만 `DeploymentBlocked`를 exit code 1로 바꾸어야 합니다. `sys.exit()`는 엔진·interlock 내부가 아니라 CLI에서만 수행하는 구조가 필요합니다.

## 5. audit-only는 여전히 파일 시스템에 씁니다

`audit_only=True`로 실행한 후 테스트 대상 폴더에서 다음 부수 효과가 확인되었습니다.

```text
.sapq_checkpoints/
.sapq_logs/
```

원인은 checkpoint와 logger를 audit-only 분기 전에 생성하고 세션 로그를 기록하기 때문입니다. 옵션 이름을 유지하려면 `NullCheckpointManager`/`NullLogger`로 완전 무쓰기 모드를 보장해야 합니다. 다른 방법은 `--state-dir`을 명시한 경우에만 상태 파일을 만들도록 하는 것입니다.

## 권고 순서

| 우선순위 | 조치 | 완료 기준 |
|---:|---|---|
| P0 | interlock에서 `strict_mode`를 실제 사용 | non-strict 호출은 decision dict 반환, process 유지 |
| P0 | CLI와 라이브러리 종료 책임 분리 | `sys.exit()`가 CLI 외부에 없음 |
| P0 | multi-vector 코어 단일화 또는 experimental 명시 | `audit_file()`이 새 코어를 사용하거나, 공개 alias에서 제거 |
| P1 | V4 반복식 수정 | 1~10행에서 마지막 이벤트 누락 없음 |
| P1 | 새 코어 hoisting 보정 이식 | 정상 FunctionDeclaration 선행 호출 통과 |
| P1 | 결과·점수·interlock 정책 단일화 | 모든 이슈가 severity/confidence에 따라 일관되게 처리 |
| P1 | audit-only 무쓰기 | 대상 인접 `.sapq_*` 산출물 없음 |

## 최종 평가

현재 최신본은 **기본 엔진의 안정성이 개선된 실행 가능한 알파**입니다. 하지만 SAPQ의 본래 차별점인 ☒ 다방향 교차 검수는 아직 새 코어에만 머물며, 그 코어도 운영 경로와 분리돼 있습니다.

따라서 지금은 새 기능을 더 추가하기보다 **‘어느 엔진이 정식 코어인가’와 ‘어떤 판정이 점수·차단으로 이어지는가’를 하나로 통일**하는 단계입니다. 그것이 완료되면 SAPQ는 다수의 보조 스캐너를 넘어, 표면적인 읽기와 오탐을 다른 관점의 증거로 반박하는 검수 시스템에 가까워질 수 있습니다.

## 부록: 재현 산출물

| 파일 | 내용 |
|---|---|
| `sapq_final_regression_output.json` | 최신본 실행 결과 |
| `sapq_final_regression.py` | 재현 스크립트 |
| `sapq_final_cli_help.txt` | CLI 진입점 검증 결과 |
