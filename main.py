# -*- coding: utf-8 -*-
"""
프로젝트 문서 자동 생성 스크립트 (v6)

기능:
- 커맨드 라인 인자(argument)로 대상 프로젝트의 루트 디렉토리 경로를 받습니다.
- 'config.json' 설정 파일을 읽어 제외할 디렉토리/파일 및 스타일을 적용합니다.
- Pygments를 사용하여 소스 코드를 문법에 맞게 하이라이팅합니다.
- 문서 상단에 클릭 가능한 목차(Table of Contents)를 추가합니다.
- 최종 결과를 WeasyPrint를 사용하여 하나의 PDF 파일로 만듭니다.

수정사항 (v6):
- 제외 목록(exclude_dirs, exclude_files) 처리에 와일드카드(*, ?) 패턴 매칭을 적용했습니다.
- 이제 .gitignore 처럼 '*.log', 'build*' 와 같은 패턴으로 유연하게 필터링할 수 있습니다.

사용법:
1. 'config.json'과 'requirements.txt' 파일이 있는지 확인합니다.
2. 터미널에서 'pip install -r requirements.txt'를 실행하여 라이브러리를 설치합니다.
3. 'python main.py [프로젝트 경로]' 형식으로 실행합니다.
4. 스크립트가 실행된 위치에 'config.json'에 정의된 이름으로 PDF 파일이 생성됩니다.
"""

# --- 종속성 임포트 ---
# 표준 라이브러리 (Standard Library)
import argparse
import fnmatch
import json
from pathlib import Path

# 서드파티 라이브러리 (Third-party Library)
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from weasyprint import HTML, CSS

# --- 설정 로드 ---
try:
    # 설정 파일을 열고 내용을 로드합니다.
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("오류: 'config.json' 파일을 찾을 수 없습니다. 스크립트를 종료합니다.")
    exit()
except json.JSONDecodeError:
    print("오류: 'config.json' 파일의 형식이 올바르지 않습니다. 스크립트를 종료합니다.")
    exit()

# 설정 값들을 변수로 할당합니다.
OUTPUT_PDF_NAME = config.get("output_pdf_name", "project_documentation.pdf")
PYGMENTS_STYLE = config.get("pygments_style", "default")
# 리스트 형태 그대로 가져옵니다 (패턴 매칭을 위해 set으로 변환하지 않음)
EXCLUDE_DIRS = config.get("exclude_dirs", [])
EXCLUDE_FILES = config.get("exclude_files", [])


def is_excluded(path: Path, root_path: Path) -> bool:
    """
    주어진 경로가 제외 패턴에 포함되는지 fnmatch를 사용하여 확인합니다.
    - 파일명: exclude_files의 와일드카드 패턴과 매칭되는지 확인
    - 디렉토리: 경로 상의 어떤 디렉토리라도 exclude_dirs 패턴과 매칭되는지 확인
    """
    # 1. 파일 이름 패턴 검사 (예: *.log, secret.*)
    # 현재 파일의 이름이 exclude_files의 패턴 중 하나라도 일치하면 제외
    if any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDE_FILES):
        return True

    # 2. 디렉토리 패턴 검사 (예: build*, temp_*)
    # 루트 경로를 기준으로 상대 경로를 구합니다.
    try:
        relative_path = path.relative_to(root_path)
    except ValueError:
        # 경로가 root_path 내부에 있지 않은 경우 (안전 장치)
        return True

    # 상대 경로의 상위 디렉토리 부분들을 순회하며 패턴 검사
    # 예: src/build_temp/main.c -> parts는 ('src', 'build_temp', 'main.c')
    # 파일명인 마지막 요소를 제외한 앞부분(디렉토리들)만 검사합니다.
    for part in relative_path.parent.parts:
        if any(fnmatch.fnmatch(part, pattern) for pattern in EXCLUDE_DIRS):
            return True

    return False


def is_binary(path: Path) -> bool:
    """
    파일이 텍스트 파일이 아닌 바이너리 파일인지 간단하게 확인합니다.
    'utf-8'로 디코딩을 시도하여 실패하면 바이너리 파일로 간주합니다.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read(1024)
        return False
    except UnicodeDecodeError:
        print(f"알림: 바이너리 파일로 추정되어 건너뜁니다 - {path}")
        return True
    except Exception as e:
        print(f"파일 읽기 오류 '{path}': {e}")
        return True


def main():
    """메인 실행 함수"""
    # 1. 커맨드 라인 인자 파서 설정 및 파싱
    parser = argparse.ArgumentParser(
        description="프로젝트 디렉토리의 파일들을 스캔하여 하나의 PDF 문서로 변환합니다."
    )
    parser.add_argument(
        "project_path",
        type=str,
        help="문서화할 프로젝트의 루트 디렉토리 경로"
    )
    args = parser.parse_args()
    project_path = Path(args.project_path)

    # 2. 경로 유효성 검사
    if not project_path.is_dir():
        print(f"오류: '{args.project_path}'는 유효한 디렉토리가 아닙니다. 스크립트를 종료합니다.")
        return

    print(f"'{project_path.resolve()}' 디렉토리에 대한 문서 생성을 시작합니다...")

    # 3. 모든 파일 탐색 및 필터링
    all_files = [p for p in project_path.rglob("*") if p.is_file()]
    # is_excluded 함수 내부 로직 변경으로 인해 와일드카드 필터링이 적용됩니다.
    target_files = [
        p for p in all_files if not is_excluded(p, project_path) and not is_binary(p)
    ]
    print(f"총 {len(target_files)}개의 파일을 처리합니다.")

    # 4. HTML 콘텐츠 및 목차 생성
    html_parts = []
    toc_items = []
    # 줄 번호 옵션 제거 유지 (AI 분석 용이성)
    formatter = HtmlFormatter(
        style=PYGMENTS_STYLE, full=True, cssclass="highlight"
    )

    for i, file_path in enumerate(target_files):
        relative_path = file_path.relative_to(project_path)
        relative_path_str = relative_path.as_posix()
        anchor = f"file-{i}"
        toc_items.append((relative_path_str, anchor))

        try:
            content = file_path.read_text(encoding="utf-8")
            try:
                lexer = get_lexer_for_filename(file_path.name, stripall=True)
            except Exception:
                lexer = TextLexer()

            highlighted_code = highlight(content, lexer, formatter)

            file_html = f"""
            <div id="{anchor}" class="file-container">
                <h2><b>{relative_path_str}</b></h2>
                {highlighted_code}
            </div>
            """
            html_parts.append(file_html)

        except Exception as e:
            print(f"'{file_path}' 처리 중 오류 발생: {e}")

    # 5. 목차(TOC) HTML 생성
    toc_html_list = [
        f"<li><a href=\"#{anchor}\">{path_str}</a></li>"
        for path_str, anchor in toc_items
    ]
    toc_html = f"""
    <div class="toc">
        <h1>{project_path.name} - 프로젝트 문서</h1>
        <h2>목차 (Table of Contents)</h2>
        <ul>
            {''.join(toc_html_list)}
        </ul>
    </div>
    """

    # 6. 전체 HTML 문서 조합 (개선된 CSS 스타일 적용 유지)
    final_css = f"""
    {formatter.get_style_defs()}
    /* --- 기본 및 타이포그래피 설정 --- */
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        font-size: 9pt;
        line-height: 1.4;
    }}
    h1, h2 {{
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        font-weight: 600;
    }}
    h1 {{ font-size: 18pt; }}
    h2 {{ font-size: 14pt; }}

    /* --- 목차(TOC) 스타일 --- */
    .toc {{
        border-bottom: 2px solid #ccc;
        padding-bottom: 20px;
        margin-bottom: 20px;
        page-break-after: always;
    }}
    .toc ul {{ list-style-type: none; padding-left: 0; }}
    .toc a {{ text-decoration: none; color: #007bff; }}
    .toc a:hover {{ text-decoration: underline; }}

    /* --- 파일 컨테이너 스타일 --- */
    .file-container {{ page-break-before: auto; }}

    /* --- 코드 하이라이팅 블록 스타일 --- */
    .highlight pre {{
        white-space: pre-wrap !important;
        word-wrap: break-word;
        font-size: 8.5pt;
        padding: 12px !important;
        border-radius: 4px;
    }}
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Project Documentation: {project_path.name}</title>
        <style>{final_css}</style>
    </head>
    <body>
        {toc_html}
        {''.join(html_parts)}
    </body>
    </html>
    """

    # 7. PDF로 변환
    output_file = Path(OUTPUT_PDF_NAME)
    print(f"'{output_file.name}' 파일로 저장 중입니다...")
    try:
        HTML(string=full_html, base_url=str(project_path)).write_pdf(
            output_file, stylesheets=[CSS(string="@page { size: A4; margin: 1.8cm; }")]
        )
        print(f"PDF 생성이 완료되었습니다! -> {output_file.resolve()}")
    except Exception as e:
        print(f"PDF 생성 중 심각한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()