# Repo Snapshot 📸

**Repo Snapshot**은 지정된 프로젝트 디렉토리의 모든 소스 코드를 스캔하여, 문법 하이라이팅이 적용된 하나의 깔끔한 PDF 문서로 생성해주는 파이썬 스크립트입니다. 코드 리뷰, 프로젝트 아카이빙, 오프라인 문서 공유 등 다양한 목적으로 활용할 수 있습니다.

---

## ✨ 주요 기능

* **자동 파일 탐색**: 지정된 프로젝트 경로 내의 모든 텍스트 기반 파일을 재귀적으로 탐색합니다.
* **지능적인 필터링**: `.git`, `node_modules` 등 불필요한 디렉토리와 바이너리 파일을 자동으로 제외합니다.
* **문법 하이라이팅**: `Pygments` 라이브러리를 사용하여 다양한 프로그래밍 언어의 문법을 아름답게 하이라이팅합니다.
* **클릭 가능한 목차**: 문서 상단에 모든 파일 목록으로 구성된 목차를 생성하여 원하는 코드로 쉽게 이동할 수 있습니다.
* **PDF 변환**: `WeasyPrint`를 통해 고품질의 PDF 문서를 생성합니다.
* **손쉬운 설정**: `config.json` 파일을 통해 제외 목록, PDF 파일 이름, 코드 스타일 등을 쉽게 변경할 수 있습니다.

---

## ⚙️ 요구 사항

* **Python 3.8** 이상

---

## 🚀 설치 및 설정

1.  **저장소 복제 또는 파일 다운로드**
    이 프로젝트의 `main.py`, `config.json`, `requirements.txt` 파일을 원하는 위치에 다운로드합니다.

2.  **필요 라이브러리 설치**
    터미널을 열고, 파일들이 위치한 디렉토리에서 아래 명령어를 실행하여 필요한 라이브러리를 설치합니다.

    ```bash
    pip install -r requirements.txt
    ```

---

## 🏃 사용법

터미널에서 `main.py` 스크립트를 실행하며, 문서화하고 싶은 프로젝트의 경로를 인자로 전달합니다.

```bash
python main.py [문서화할 프로젝트 경로]
```

#### 실행 예시

* **절대 경로 사용:**
    ```bash
    python main.py /Users/dev/my-awesome-project
    ```

* **상대 경로 사용:**
    ```bash
    python main.py ../my-other-project
    ```

* **현재 디렉토리를 대상으로 지정:**
    ```bash
    python main.py .
    ```

스크립트 실행이 완료되면, 스크립트가 위치한 폴더에 `config.json`에 설정된 이름으로 PDF 파일이 생성됩니다.

---

## 🔧 설정 (`config.json`)

`config.json` 파일을 수정하여 프로그램의 동작을 제어할 수 있습니다.

```json
{
  "output_pdf_name": "project_documentation.pdf",
  "pygments_style": "monokai",
  "exclude_dirs": [
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv"
  ],
  "exclude_files": [
    "project_documentation.pdf",
    "main.py",
    "config.json",
    "requirements.txt"
  ]
}
```

* `output_pdf_name`: 생성될 PDF 파일의 이름을 지정합니다.
* `pygments_style`: 코드 하이라이팅 테마를 지정합니다. ([사용 가능한 스타일 목록](https://pygments.org/styles/))
* `exclude_dirs`: 문서에 포함하지 않을 디렉토리 이름 목록입니다.
* `exclude_files`: 문서에 포함하지 않을 파일 이름 목록입니다.

---

## 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)를 따릅니다.
