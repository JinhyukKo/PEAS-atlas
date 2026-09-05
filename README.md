# LinPEAS Atlas

`peas2json.py`의 섹션·ANSI 색상 규칙을 바탕으로 LinPEAS 결과를 브라우저에서 탐색하는 단일 파일 웹 서버입니다. Python 표준 라이브러리만 사용하므로 별도 패키지 설치가 없습니다.

## 실행

```bash
python3 server.py --port 8080
```

다른 PC에서 접속하려면 서버 PC의 방화벽에서 TCP 8080을 허용하고 `http://서버IP:8080`으로 접속합니다.

PowerShell에서는 현재 폴더의 배치 파일 앞에 `./` 또는 `.\\`를 붙여 실행합니다.

```powershell
.\run.bat --port 8080
```

또는 Windows Python Launcher가 설치되어 있다면 다음 명령을 사용합니다.

```powershell
py server.py --port 8080
```

## 사용

기본 폴더의 `result.txt`가 자동으로 표시됩니다. 다른 결과는 **결과 파일 업로드**로 올리면 됩니다. `peas2json.py`가 생성한 JSON도 직접 올릴 수 있습니다.

왼쪽 사이드바에는 카테고리와 하위 섹션이 트리로 표시됩니다. 최상위 카테고리 이름을 클릭하면 하위 섹션 목록이 열리고, 다시 클릭하면 닫힙니다. 하위 섹션을 선택하면 해당 카테고리는 자동으로 열리고 다른 카테고리는 닫히는 아코디언 방식입니다. 사이드바에서는 ATT&CK 기술 ID를 제외한 섹션 이름만 표시합니다. 항목을 클릭하면 해당 섹션과 상위 경로만 남겨 결과를 필터링하고 위치로 부드럽게 이동합니다. 검색은 선택된 섹션 안의 세부 결과를 필터링하며, 검색어가 있는 카테고리만 사이드바에 남깁니다. 원본 ANSI 색상은 결과 텍스트에 그대로 재현되며, ALL·REDYELLOW·RED·YELLOW·GREEN 등의 버튼을 복수 선택해 해당 색 신호만 볼 수 있습니다. 구조화 JSON 다운로드를 지원합니다. 업로드 내용은 서버 메모리에서만 처리하며 파일로 저장하지 않습니다.

알려진 MITRE ATT&CK Enterprise 기술 ID는 제목에서 기술명과 공식 ATT&CK 페이지 링크로 확장됩니다. 예: `T1548.003 · Abuse Elevation Control Mechanism: Sudo and Sudo Caching`.

기술 ID에 연결된 MITRE ATT&CK 전술(Tactic)은 섹션 제목에 배지로 표시됩니다. `Discovery`, `Privilege Escalation`, `Credential Access` 등의 전술을 복수 선택해 관련 섹션만 필터링할 수 있습니다.
# PEAS-atlas
